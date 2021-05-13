# dataPipeline Scripts
In this directory are a number of scripts to run the gc_ingest package 
in dev, dependent on the type of task that needs to be completed. The
required inputs for each and the corresponding images used for the docker 
containers script are listed at the top of the .sh files. Information 
of the CLI commands called to run the scripts can be found in 
`/gc_ingest/core/cli.py`.

The scripts include:
* **checkpoint_ingest.sh**: script that grabs the latest checkpoint from 
  s3 and parses/ingests from a local directory. This is the main 
  gc_ingest function used in production, and this script is important 
  to mirror production's pipeline.
  

* **crawl_and_ingest.sh**: the main ingest script consisting of three docker runs: 
  the first checks that the connections to the databases are 
  functional, the second runs the crawl+download, and the third performs
  the ingests in neo4j, ElasticSearch, postgres, and s3.
  

* **neo4j_reingest.sh**: This script pulls down documents from s3's `json` directory
  (jsons resulting from the corpus parse) and reingests them into 
  the neo4j database, all in a docker container.  
  

* **reindex.sh**: pulls down documents from s3's `json` directory
  (jsons resulting from the corpus parse) and reingests the results 
  into ElasticSearch.
  

* **reparse.sh**: pulls down documents from s3's `pdf` directory 
  (raw pdfs/metadata), parses them, reingests the output into neo4j and
  ElasticSearch, then pushes the output into s3's `json` directory.
  
There are two other scripts that are not related to ingests but are needed
for testing purposes and for email notifications:

* **parse.sh**: parses a given directory of raw pdfs/metadata to a specified
  output directory. This basically just calls the _common.document_parser pdf-to-json_ function.
  

* **email_notifications_utils.sh**: a script that's sourced in _run_prod_gc_crawler_downloader.sh_
  to send email notifications for crawler statuses when ingests are run.
  
# How to get the scripts running
Near the top of each script are five parameters that are often changed, including;
* HOST_REPO_DIR: the path to the local repository that you're running the script
  from. 
* DEPLOYMENT_ENV: whether to run in dev or prod environment
* TEST_RUN: whether to perform a test run, which only crawls the first
  two documents of `us_code`
* INDEX_NAME: the name of the elasticsearch index to ingest 
* ALIAS_NAME: the alias of the elasticsearch index to ingest

Other parameters that aren't often adjusted, such as the image names/python
command in the continer/number of threads to parse and OCR should be 
adjusted dependent on the given situation.

The input parameters needed to run each script are described in comments
at the top of each respective file (e.g. neo4j_reingest.sh requires 3 inputs,
the job.log path, container name, and job directory, while crawl_and_ingest requires
4 inputs, including the above and the crawl_output directory)

* format for running neo4j_reingest.sh: `bash crawl_and_ingest.sh {path_to_job_log} {container_name}
  {path_to_job_directory}`
  
* example for running neo4j_reingest.sh: `bash crawl_and_ingest.sh /data/pub_update_jobs/2021-04-29-image-test/job.log full_pipeline /data/pub_update_jobs/2021-04-29-image-test/job_output/`


* format for running crawl_and_ingest.sh: `bash crawl_and_ingest.sh {path_to_job_log} {container_name} {path_to_crawl_directory}
  {path_to_job_directory}`

* example for running crawl_and_ingest.sh: `bash crawl_and_ingest.sh /data/pub_update_jobs/2021-04-29-image-test/job.log full_pipeline /data/pub_update_jobs/2021-04-29-image-test/crawl_output/ /data/pub_update_jobs/2021-04-29-image-test/job_output/`

