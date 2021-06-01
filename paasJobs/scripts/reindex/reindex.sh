#!/usr/bin/env bash

set -o errexit
set -o nounset
set -o pipefail

# always set in stage params

readonly SCRIPT_PARENT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
readonly SETTINGS_CONF_PATH="$SCRIPT_PARENT_DIR/settings.conf"

#####
## ## LOAD SETTINGS
#####

source "$SETTINGS_CONF_PATH"

# always set in stage params
SCRIPT_ENV=${SCRIPT_ENV:-local}

# Check basic params
case "$SCRIPT_ENV" in
prod)
  echo "RUNNING IN PROD ENV"
  ;;
dev)
  echo "RUNNING IN DEV ENV"
  ;;
local)
  echo "RUNNING IN LOCAL ENV"
  ;;
*)
  echo >&2 "Must set SCRIPT_ENV = (prod|dev|local)"
  exit 2
  ;;
esac

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

function setup_venv_and_other_commands() {

  source "/opt/gc-venv-current/bin/activate"
  export PATH="$PATH:/usr/local/bin"

  case "$SCRIPT_ENV" in
  prod)
    export AWS_DEFAULT_REGION="us-gov-west-1"
    AWS_CMD="aws"
    ;;
  dev)
    export AWS_DEFAULT_REGION="us-east-1"
    AWS_CMD="aws"
    ;;
  local)
    export AWS_DEFAULT_REGION="us-east-1"
    AWS_CMD="aws --endpoint-url http://s3-server:9000"
    ;;
  *)
    echo >&2 "Must set SCRIPT_ENV = (prod|dev|local)"
    exit 2
    ;;
  esac

}

function setup_app_config_copy() {
  echo "FETCHING APP CONFIG"
  S3_APP_CONFIG_PATH="${S3_BUCKET_NAME}/${APP_CONFIG_BASE_PREFIX}${APP_CONFIG_FILENAME}"
  LOCAL_APP_CONFIG_PATH="${LOCAL_GC_REPO_BASE_DIR}/configuration/app-config/${APP_CONFIG_NAME:-$SCRIPT_ENV}.json"

  $AWS_CMD s3 cp "s3://${S3_APP_CONFIG_PATH}" "$LOCAL_APP_CONFIG_PATH"
}

function setup_topic_models_copy() {
  echo "FETCHING TOPIC MODEL"
  S3_TOPIC_MODEL_PATH="${S3_BUCKET_NAME}/${TOPIC_MODEL_DIR}"
  LOCAL_TOPIC_MODEL_PATH="${LOCAL_GC_REPO_BASE_DIR}/dataScience/models/topic_models/models/"

  mkdir -p "${LOCAL_TOPIC_MODEL_PATH}"
  $AWS_CMD s3 cp --recursive "s3://${S3_TOPIC_MODEL_PATH}" "${LOCAL_TOPIC_MODEL_PATH}"
}

function setup_local_vars_and_dirs() {

  LOCAL_JOB_DIR="$LOCAL_TMP_DIR/job"
  LOCAL_GC_REPO_BASE_DIR="$LOCAL_GC_REPO_BASE_DIR"

  mkdir -p "$LOCAL_JOB_DIR"
  mkdir -p "$LOCAL_GC_REPO_BASE_DIR"

  # setup logs
  JOB_TS=$(sed 's/.\{5\}$//' <<< $(date --iso-8601=seconds))
  S3_JOB_LOG_PREFIX="gamechanger/data-pipelines/orchestration/logs/${JOB_NAME}/${JOB_TS}/"
  LOCAL_JOB_LOG_PATH="$LOCAL_TMP_DIR/job.log"
  touch "$LOCAL_JOB_LOG_PATH"

  # setup pythonpath & cwd
  export PYTHONPATH="$LOCAL_GC_REPO_BASE_DIR"
  cd "$LOCAL_GC_REPO_BASE_DIR"
}

function configure_repo() {
  local es_config_name="${ES_CONFIG_NAME:-$SCRIPT_ENV}"
  local app_config_name="${APP_CONFIG_NAME:-$SCRIPT_ENV}"
  python -m configuration init "$SCRIPT_ENV" \
  	--app-config "$app_config_name" --elasticsearch-config "$es_config_name"
  python -m configuration init "$SCRIPT_ENV" \
  	--app-config "$app_config_name" --elasticsearch-config "$es_config_name"
  python -m configuration check-connections
}

#####
## ## MAIN COMMANDS
#####

function run_core_ingest() {

  local job_dir="$LOCAL_JOB_DIR"
  local job_ts="$JOB_TS"

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
    --max-ocr-threads="$max_ocr_threads" \
    --skip-revocation-update="$skip_revocation_update" \
    reindex

}

#####
## ## POST COMMANDS
#####

function copy_logs_to_s3() {
  $AWS_CMD s3 cp "$LOCAL_JOB_LOG_PATH" s3://"$S3_BUCKET_NAME/$S3_JOB_LOG_PREFIX"
}

##### ##### #####
## ## ## ## ## ## ACTUAL EXEC FLOW
##### ##### #####

# setup
setup_venv_and_other_commands
echo_tmp_dir_locaton
setup_local_vars_and_dirs
# LOCAL_JOB_LOG_PATH var is now set
setup_app_config_copy 2>&1 | tee -a "$LOCAL_JOB_LOG_PATH"
setup_topic_models_copy 2>&1 | tee -a "$LOCAL_JOB_LOG_PATH"
configure_repo 2>&1 | tee -a "$LOCAL_JOB_LOG_PATH"

SECONDS=0
cat <<EOF 2>&1 | tee -a "$LOCAL_JOB_LOG_PATH"

  STARTING PIPELINE RUN
  $(date "+DATE: %Y-%m-%d TIME: %H:%M:%S")

EOF

# main
run_core_ingest 2>&1 | tee -a "$LOCAL_JOB_LOG_PATH"


cat <<EOF 2>&1 | tee -a "$LOCAL_JOB_LOG_PATH"

  SUCCESSFULLY FINISHED PIPELINE RUN
  $(date "+DATE: %Y-%m-%d TIME: %H:%M:%S")

EOF

# how long?
duration=$SECONDS
echo -e "\n $(($duration / 60)) minutes and $(($duration % 60)) seconds elapsed." 2>&1 | tee -a "$LOCAL_JOB_LOG_PATH"

# flush logs
copy_logs_to_s3
