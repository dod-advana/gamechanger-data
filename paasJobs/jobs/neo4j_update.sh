#!/usr/bin/env bash

set -o errexit
set -o nounset
set -o pipefail

#####
## ## MAIN COMMANDS
#####

function run_core_neo4j_update() {
  local job_dir="$LOCAL_TMP_DIR"
  local job_ts="$JOB_TS"

  local bucket_name="$S3_BUCKET_NAME"

  local es_index_name="$ES_INDEX_NAME"
  local es_alias_name="${ES_ALIAS_NAME:-}"

  local skip_neo4j_update="$SKIP_NEO4J_UPDATE"
  local skip_snapshot_backup="$SKIP_SNAPSHOT_BACKUP"
  local skip_db_backup="$SKIP_DB_BACKUP"
  local skip_db_update="$SKIP_DB_UPDATE"
  local skip_revocation_update="$SKIP_REVOCATION_UPDATE"
  local skip_es_revocation="yes"

  local max_ocr_threads="${MAX_OCR_THREADS_PER_FILE:-4}"
  local max_parser_threads="${MAX_PARSER_THREADS:-16}"
  local max_neo4j_threads="${MAX_PARSER_THREADS:-16}"
  local max_s3_threads="${MAX_S3_THREADS:-32}"

  local current_snapshot_prefix="bronze/gamechanger/"
  local backup_snapshot_prefix="bronze/gamechanger/backup/"
  local load_archive_base_prefix="bronze/gamechanger/load-archive/"
  local db_backup_base_prefix="bronze/gamechanger/backup/db/"

  python -m dataPipelines.gc_ingest pipelines core ingest \
    --skip-neo4j-update="$skip_neo4j_update" \
    --skip-snapshot-backup="$skip_snapshot_backup" \
    --skip-db-backup="$skip_db_backup" \
    --skip-db-update="$skip_db_update" \
    --current-snapshot-prefix="$current_snapshot_prefix" \
    --backup-snapshot-prefix="$backup_snapshot_prefix" \
    --db-backup-base-prefix="$db_backup_base_prefix" \
    --load-archive-base-prefix="$load_archive_base_prefix" \
    --bucket-name="$bucket_name" \
    --job-dir="$job_dir" \
    --batch-timestamp="$job_ts" \
    --index-name="$es_index_name" \
    --alias-name="$es_alias_name" \
    --max-threads="$max_parser_threads" \
    --max-ocr-threads="$max_ocr_threads" \
    --max-s3-threads="$max_s3_threads" \
    --skip-revocation-update="$skip_revocation_update" \
    --skip-es-revocation="$skip_es_revocation" \
    update-neo4j
}

##### ##### #####
## ## ## ## ## ## ACTUAL EXEC FLOW
##### ##### #####

SECONDS=0
cat <<EOF

  STARTING PIPELINE RUN
  $(date "+DATE: %Y-%m-%d TIME: %H:%M:%S")

EOF

# main
run_core_neo4j_update

cat <<EOF

  SUCCESSFULLY FINISHED PIPELINE RUN
  $(date "+DATE: %Y-%m-%d TIME: %H:%M:%S")

EOF

# how long?
duration=$SECONDS
echo -e "\n $(( $SECONDS / 3600 ))h $(( ($SECONDS % 3600)/60 ))m $(($SECONDS % 60))s elapsed."

