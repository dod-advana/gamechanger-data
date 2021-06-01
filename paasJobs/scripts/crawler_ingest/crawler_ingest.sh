#!/usr/bin/env bash

set -o errexit
set -o nounset
set -o pipefail

# always set in stage params

readonly SCRIPT_PARENT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

#####
## ## SETUP TMP DIR
#####

function setup_tmp_dir() {
  LOCAL_TMP_DIR=$(mktemp -d)
}
setup_tmp_dir # CALLING RIGHT AWAY (to avoid issues with unbound var later)

function echo_tmp_dir_locaton() {
  echo "TEMP DIR IS AT $LOCAL_TMP_DIR"
}

function remove_tmp_dir() {
  if [[ -d "$LOCAL_TMP_DIR" ]]; then
    rm -r "$LOCAL_TMP_DIR"
  fi
}

#####
## ## REGISTER CLEANUP HOOKS
#####

function cleanup_hooks() {
  remove_tmp_dir
  # echo_tmp_dir_locaton
}
if [[ "${CLEANUP:-yes}" == "no" ]]; then
  trap cleanup_hooks EXIT
fi

#####
## ## SETUP COMMANDS
#####

function setup_venv() {

  source "/opt/gc-venv-current/bin/activate"
  export PATH="$PATH:/usr/local/bin"

}

function setup_local_vars_and_dirs() {

  LOCAL_JOB_DIR="$LOCAL_TMP_DIR/job"
  LOCAL_GC_REPO_BASE_DIR="$LOCAL_GC_REPO_BASE_DIR"

  mkdir -p "$LOCAL_JOB_DIR"
  mkdir -p "$LOCAL_GC_REPO_BASE_DIR"

  # setup pythonpath & cwd
  export PYTHONPATH="$LOCAL_GC_REPO_BASE_DIR"
  cd "$LOCAL_GC_REPO_BASE_DIR"
}

#####
## ## MAIN COMMANDS
#####

function run_core_ingest() {

  local job_dir="$LOCAL_JOB_DIR"
  local job_ts="$(sed 's/.\{5\}$//' <<< $(date --iso-8601=seconds))"

  local crawler_output="$job_dir/$RELATIVE_CRAWLER_OUTPUT_LOCATION"

  local bucket_name="$S3_BUCKET_NAME"

  local es_index_name="$ES_INDEX_NAME"
  local es_alias_name="${ES_ALIAS_NAME:-}"

  local skip_neo4j_update="$SKIP_NEO4J_UPDATE"
  local skip_snapshot_backup="$SKIP_SNAPSHOT_BACKUP"
  local skip_db_backup="$SKIP_DB_BACKUP"
  local skip_db_update="$SKIP_DB_UPDATE"
  local skip_revocation_update="$SKIP_REVOCATION_UPDATE"

  local max_ocr_threads="${MAX_OCR_THREADS_PER_FILE:-4}"
  local max_parser_threads="${MAX_PARSER_THREADS:-16}"
  local max_neo4j_threads="${MAX_PARSER_THREADS:-16}"

  local current_snapshot_prefix="gamechanger/"
  local backup_snapshot_prefix="gamechanger/backup/"
  local load_archive_base_prefix="gamechanger/load-archive/"
  local db_backup_base_prefix="gamechanger/backup/db/"

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
    --max-threads-neo4j="$max_neo4j_threads" \
    --max-ocr-threads="$max_ocr_threads" \
    --crawler-output="$crawler_output" \
    --skip-revocation-update="$skip_revocation_update" \
    checkpoint \
    --checkpoint-limit=1 \
    --checkpoint-file-path="gamechanger/external-uploads/crawler-downloader/checkpoint.txt" \
    --checkpointed-dir-path="gamechanger/external-uploads/crawler-downloader/" \
    --checkpoint-ready-marker="manifest.json" \
    --advance-checkpoint="yes"

}

##### ##### #####
## ## ## ## ## ## ACTUAL EXEC FLOW
##### ##### #####

# setup
setup_venv
echo_tmp_dir_locaton
setup_local_vars_and_dirs
# LOCAL_JOB_LOG_PATH var is now set
SECONDS=0
cat <<EOF

  STARTING PIPELINE RUN
  $(date "+DATE: %Y-%m-%d TIME: %H:%M:%S")

EOF

# main
run_core_ingest


cat <<EOF

  SUCCESSFULLY FINISHED PIPELINE RUN
  $(date "+DATE: %Y-%m-%d TIME: %H:%M:%S")

EOF

# how long?
duration=$SECONDS
echo -e "\n $(($duration / 60)) minutes and $(($duration % 60)) seconds elapsed."

