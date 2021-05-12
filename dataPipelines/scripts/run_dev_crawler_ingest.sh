readonly INGEST_DIR="/data/pub_update_jobs/2021-05-12-fullingest/
mkdir $INGEST_DIR && mkdir $INGEST_DIR/crawl_output && mkdir $INGEST_DIR/job_output
bash crawl_and_ingest.sh "$INGEST_DIR/job.log" fullingest "$INGEST_DIR/crawl_output" "$INGEST_DIR/job_output" 
