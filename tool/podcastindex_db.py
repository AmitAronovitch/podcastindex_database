#!/usr/bin/env python3
from pathlib import Path
from typing import List
from contextlib import contextmanager
from functools import cached_property
import sqlite3
import tarfile

import tqdm
import requests
import typer

PI_DOWNLOAD_URL = 'https://public.podcastindex.org/podcastindex_feeds.db.tgz'
DEFAULT_CHUNK_SIZE = 5 * (1 << 20)  # 5MiB
PI_FNAME = PI_DOWNLOAD_URL.split('/')[-1]
PI_DB_NAME = Path(PI_FNAME).stem

app = typer.Typer()


@contextmanager
def statements_progress(expected_statements, connection, n_statements=1000, show_progress=True):
    """
    progress bar context for long SQL operations. Counts statements of the SQL VM.
    We need to know in advance the expected number of statements for the total operation.
    (probably can be estimated empirically, as a function of the total processed records).
    """
    pbar = tqdm.tqdm(total=expected_statements, disable=not show_progress)

    def update():
        pbar.update(n_statements)

    connection.set_progress_handler(update, n_statements)
    try:
        yield pbar
    finally:
        pbar.close()
        connection.set_progress_handler(None, 0)


class SearchDB:
    """
    DB Client for searching on specific fields in some table
    Supports building the index (FTS table) and the search itself.
    """
    TABLE = 'podcasts'
    SEARCH_FIELDS = ['title', 'description']
    OUT_FIELDS = ['id', 'podcastGuid', 'title']

    # SQL templates
    CREATE_FTS = """\
CREATE VIRTUAL TABLE {table}_fts
USING fts5 (
   id, {fields}
)
"""
    POPULATE_FTS = """\
INSERT INTO {table}_fts (id, {fields})
  SELECT id, {fields} FROM {table}
"""
    COUNT = """\
SELECT COUNT(*) FROM {table}
"""
    SEARCH = """\
SELECT {out_fields}
FROM {table} p INNER JOIN {table}_fts f ON p.id = f.id
WHERE {table}_fts MATCH ('{{{fields}}}:' || ?)
"""
    def __init__(self, db: Path, table=TABLE, fields=SEARCH_FIELDS):
        self.table = table
        self.fields = fields
        self.con = sqlite3.connect(db)

    @property
    def comma_separated_fields(self):
        return ', '.join(self.fields)

    @cached_property
    def cursor(self):
        return self.con.cursor()

    def reset_cursor(self):
        self.cursor.close()
        del self.cursor

    def _exec(self, sql: str, bindings: tuple[str]=()):
        return self.cursor.execute(sql, bindings)

    def count_records(self):
        recs = list(self._exec(self.COUNT.format(table=self.table)))
        assert len(recs) == 1  # TODO: raise proper error
        count, = recs[0]
        return count

    def create_fts(self):
        sql = self.CREATE_FTS.format(table=self.table, fields=self.comma_separated_fields)
        self._exec(sql)

    def populate_fts(self, show_progress=False):
        statements_per_record = 50.6  # estimated...
        update_rate = 1000  # config

        num_records = self.count_records()
        expected_total = int(num_records * statements_per_record)
        sql = self.POPULATE_FTS.format(table=self.table, fields=self.comma_separated_fields)
        with statements_progress(expected_total, self.con, update_rate, show_progress):
            self._exec(sql)
        self.con.commit()

    def search(self, term: str, out_fields=OUT_FIELDS, fields=None):
        if fields is None:
            fields = self.fields
        assert set(fields).issubset(self.fields)  # TODO: raise proper error
        fields_str = ' '.join(fields)
        out_fields_str = ', '.join(f'p.{field}' for field in out_fields)
        sql = self.SEARCH.format(table=self.table, fields=fields_str, out_fields=out_fields_str)
        return self._exec(sql, (term,))


@app.command()
def download(url: str=PI_DOWNLOAD_URL, path: Path=Path(PI_FNAME), chunk_size: int=DEFAULT_CHUNK_SIZE, show_progress: bool=True):
    res = requests.get(url, stream=True)
    res.raise_for_status()
    size = int(res.headers['content-length'])

    pbar = tqdm.tqdm(total=size, unit='iB', unit_scale=True, disable=not show_progress)
    with path.open('wb') as f:
        for chunk in res.iter_content(chunk_size=chunk_size):
            pbar.update(len(chunk))
            f.write(chunk)
    pbar.close()


@app.command()
def unpack_db(path: Path=Path(PI_FNAME), db_name: str=PI_DB_NAME, out_path: Path=Path()):
    print(f'extracting db from archive {path}')
    with path.open('rb') as f:
        tar = tarfile.open(mode='r:gz', fileobj=f)
        member_name = f'./{db_name}'
        info = tar.getmember(member_name)
        print(f'extracting {info.name} size={info.size}')
        tar.extract(member_name, path=out_path)


@app.command()
def setup_fts(
        db: Path=Path(PI_DB_NAME), table: str=SearchDB.TABLE, fields: List[str]=SearchDB.SEARCH_FIELDS,
        show_progress: bool=True):
    client = SearchDB(db, table, fields)
    print(f'total {client.count_records()} records in {table} table')
    print(f'creating FTS table for {client.comma_separated_fields}')
    client.create_fts()
    print(f'populating {table}_fts')
    client.populate_fts(show_progress)
    # TODO: need to setup triggers...


@app.command()
def search(
        term: str,
        out_fields: List[str]=SearchDB.OUT_FIELDS,
        db: Path=Path(PI_DB_NAME), table: str=SearchDB.TABLE, fields: List[str]=SearchDB.SEARCH_FIELDS):
    client = SearchDB(db, table, fields)
    for res in client.search(term, out_fields, fields):
        print(res)


if __name__ == '__main__':
    app()
