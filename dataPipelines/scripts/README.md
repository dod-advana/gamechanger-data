## dataPipeline Scripts
In this directory are a number of scripts to run the gc_ingest package 
in dev, dependent on the type of task that needs to be completed. The
required inputs for each script are listed at the top of the .sh files,
while the corresponding images used for the docker containers are set
as variables at the top of the scripts. Information of the CLI commands
called to run the scripts can be found in gc_ingest/core/cli.py.

The scripts include:
* **crawl_and_ingest.sh**: the main ingest script consisting of three docker runs: 
  the first checks that the connections to the databases are 
  functional, the second runs the crawl+download, and the third performs
  the ingests.
  
* **neo4j_reingest**: This script pulls down documents from s3's json directory
  (jsons resulting from the corpus parse) and reingests them into 
  the neo4j database, all in a docker container.  
  
* **reindex.sh**: pulls down documents from s3's json directory
  (jsons resulting from the corpus parse) and reingests the results 
  into ElasticSearch.
  
* **reparse.sh**: pulls down documents from s3's pdf directory 
  (raw pdfs/metadata), parses them, reingests the output into neo4j and
  ElasticSearch, then pushes the output into s3's json directory.
  
There are two other scripts that are not related to ingests but are needed
for testing purposes and for email notifications:

* **parse.sh**: parses a given directory of raw pdfs/metadata to a specified
  output directory. This basically just calls the _common.document_parser pdf-to-json_ function.
  
* **email_notifications_utils.sh**: a script that's sourced in _run_prod_gc_crawler_downloader.sh_
  to send email notifications for crawler statuses when ingests are run.