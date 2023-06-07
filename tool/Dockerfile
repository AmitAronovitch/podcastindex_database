FROM python:3.11-slim
COPY requirements_script.txt /tmp/
RUN pip install -r /tmp/requirements_script.txt
COPY podcastindex_db.py /usr/local/bin/podcastindex_db
WORKDIR /data
ENTRYPOINT ["podcastindex_db"]
CMD ["--help"]
