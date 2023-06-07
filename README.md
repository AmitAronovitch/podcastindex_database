# Database

This is the main place for database related information, work, exports, etc.

Download our full podcast database as a sqlite3 file [over IPFS](https://cloudflare-ipfs.com/ipns/k51qzi5uqu5dkde1r01kchnaieukg7xy9i6eu78kk3mm3vaa690oaotk1px6wo/podcastindex_feeds.db.tgz) or [using HTTP](https://public.podcastindex.org/podcastindex_feeds.db.tgz).

# Sample export of the "newsfeeds" table

Most of the field names are obvious.  But, for clarity, here are the meanings of others:

* lastcheck - The last time the feed was pulled (successfully or not) by the [aggrivate](https://github.com/Podcastindex-org/aggregator) app.
* lastupdate - The channel level pubdate if we can determine one.
* lastmod - The value of the http "Last-Modified" header on the last pull.
* errors - Errors encountered by aggrivate when pulling.
* updated - A flag set by aggrivate to let the parser know if the feed has updated content it should parse.  This is set to the node id 
            that the current copy of aggrivate is running on.  This node id number is how the parser knows which node the file containing the new
            feed content lives on.
* lastitemid - Not currently used.
* pubdate - Not currently used.
* contenthash - An MD5 hash of the current feed content
* dead - The feed has had too many errors and should not be checked anymore
* original_url - The url of this feed when it was first added to the database.
* artwork_url_600 - Sometimes we can get a hi-res image url from itunes.  If so, it lives here.
* type - 0 = RSS, 1 = ATOM
* parse_errors - The number of errors encountered while parsing the feed
* pullnow - This is a flag. If set to 1, aggrivate will always pull it first before anything else.
* parsenow - This is a flag. If set to 1, partytime will parse this feed first before anything else.
* newest_item_pubdate - The unix timestamp of the newest item we could find in the feed.
* update_frequency - Set to a number 1-9 based on the interval between what "newest_item_pubdate" is now and what "newest_item_pubdate" was before 
                     that.  The smaller the number, the shorter that interval was.
* priority - This is a flag.  Some podcasts are just really popular and need to be checked frequently to make sure they aren't missed.  This can be 
             set manually or through automated popularity discovery.
* detected_language - Not used yet.

# podcastindex_db - Helper for downloading and Manipulating a local sqlite3 index

## Install using docker

For bash shell, create the following alias
```bash
alias podcastindex_db='docker run --rm -it --user $(id -u):$(id -g) -v /tmp:/tmp -v ${PWD}:/data amitar/podcastindex_db'
```
(to make this alias permanent, you can add that line to the relevant file, depending on your distro. Usually that is either ~/.bash_aliases or ~/.bashrc)

Now, when you type `podcastindex_db` for the first time, it will download the image from dockerhub, and display the commandline help.

## Usage

1. Go to the directory where you want to store the database
```bash
mkdir pi_data
cd pi_data
```

2. Download and extract the database
```bash
podcastindex_db download
podcastindex_db unpack-db
```
(use `podcastindex_db download --help` and `podcastindex_db unpack-db --help` to see more options. This is useful if you are
storing multiple versions of the db, or resetting the live db by unpacking from the saved backup).

3. Create a full-text-search index.
```
podcastindex_db setup-fts
```
The default indexes the `title` and `description` fields only, but if you intend to search other fields
you need to specify them using (possibly multiple) `--fields` parameters (see `podcastindex_db setup-fts --help` for more options).

4. Search...
```bash
~$ podcastindex_db search --fields title "100 retro live"
(4578888, '9a5c8e19-3c5e-534e-a2a2-378c740c8a2e', 'Podcasts Live – La Caz Retro – Le Podcast 100% retrogaming')
(5718023, '27293ad7-c199-5047-8135-a864fb546492', '100% Retro - Live 24/7')
(6367704, '27293ad7-c199-5047-8135-a864fb546491', '100% Retro - Live 24/7 (MegaCRON!)')

~$ podcastindex_db search --out-fields id --out-fields title --out-fields itunesAuthor --fields title "podcasting 2 0" 
(41423, 'Podcasting “StranieroVision “ &amp; “Radio Guaglione!”', 'The Straniero')
(199493, "Podcasting Ain't Easy 2.0", 'Merick Studios')
(920666, 'Podcasting 2.0', 'Podcast Index LLC')
(1067279, 'face for podcasting', 'Steven Mandzk')
(1370495, 'podCast411 -  Learn about Podcasting and Podcasters - The Podcast 2.0 feed', 'Rob @ podcast411 covering podcasters and podcasting news')
(2372494, 'DecimoA - Podcasting Limited', 'DecimoA - Podcasting Limited S')
(2972343, 'Rochester Prep High School HS 2.0: Podcasting', 'Rochester Prep High School HS 2.0: Podcasting')
(4162593, 'The Future of Podcasting', 'Dave Jackson & Daniel J. Lewis')
(5790180, 'Podcasting and the Blockchain', 'Jennifer Navarrete')
```

Everything in this repo is under the [MIT](https://opensource.org/licenses/MIT) license.
