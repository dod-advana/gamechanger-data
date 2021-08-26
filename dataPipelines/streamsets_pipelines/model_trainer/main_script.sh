#!/usr/bin/env bash

set -o errexit
set -o nounset
set -o pipefail

# always set in stage params
SCRIPT_ENV=${SCRIPT_ENV:-dev}

# Check basic params
case "$SCRIPT_ENV" in
test)
  echo "RUNNING IN TEST ENV"
  ;;
prod)
  echo "RUNNING IN PROD ENV"
  ;;
dev)
  echo "RUNNING IN DEV ENV"
  ;;
*)
  echo >&2 "Must set SCRIPT_ENV = (prod|dev|test)"
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
trap cleanup_hooks EXIT

#####
## ## SETUP LOCAL WORK DIRECTORIES
#####

function setup_local_vars_and_dirs() {

  if [[ "$SCRIPT_ENV" == "dev" ]]; then
    LOCAL_GC_REPO_BASE_DIR="/home/sdc/app-repo"
  else
    LOCAL_GC_REPO_BASE_DIR="$LOCAL_TMP_DIR/app-repo"
  fi

  LOCAL_GC_REPO_TGZ_PATH="$LOCAL_GC_REPO_BASE_DIR/repo.tgz"
  LOCAL_CORPUS_DIR_PATH="$LOCAL_TMP_DIR/corpus"
  LOCAL_BASE_MODEL_DIR_PATH="$LOCAL_TMP_DIR/models"
  LOCAL_JOB_LOG_PATH="$LOCAL_TMP_DIR/job.log"

  mkdir -p "$LOCAL_GC_REPO_BASE_DIR"
  mkdir -p "$LOCAL_CORPUS_DIR_PATH"
  mkdir -p "$LOCAL_BASE_MODEL_DIR_PATH"

}

#####
## ## SETUP COMMANDS & DIRS
#####

function init_prod_key_tab() {
  USE_KEYTAB="${USE_KEYTAB:-true}"
  if [[ "$USE_KEYTAB" == "true" ]]; then
    kinit -k -t "/etc/security/keytabs/streamsets.keytab" "${KRB_NAME}"
  fi
}

function setup_aws_and_python_exec_commands() {

  case "$SCRIPT_ENV" in
  test|prod)
    export AWS_DEFAULT_REGION="us-gov-west-1"
    PYTHON_CMD="/opt/gc-venv/bin/python"
    AWS_CMD="aws"
    ;;
  dev)
    export AWS_DEFAULT_REGION="us-east-1"
    PYTHON_CMD="/home/sdc/app-venv/bin/python"
    AWS_CMD="aws --endpoint-url http://s3-server:9000"
    ;;
  *)
    echo >&2 "Must set SCRIPT_ENV = (prod|dev|test)"
    exit 2
    ;;
  esac

}

function setup_local_repo_copy() {

  if [[ "$SCRIPT_ENV" == "dev" ]]; then
    if [[ $(ls -A "$LOCAL_GC_REPO_BASE_DIR") ]]; then
      echo "LOCAL REPO dir should be mounted at: $LOCAL_GC_REPO_BASE_DIR"
      return 0
    else
      echo &>2 "LOCAL REPO dir appears empty: $LOCAL_GC_REPO_BASE_DIR"
      exit 1
    fi
  fi

  echo "FETCHING REPO"
  $AWS_CMD s3 cp "s3://$S3_GC_REPO_TGZ_PATH" "$LOCAL_GC_REPO_TGZ_PATH"

  tar -xzf "$LOCAL_GC_REPO_TGZ_PATH" -C "$LOCAL_GC_REPO_BASE_DIR"

}

function change_into_local_repo_dir() {
  cd "$LOCAL_GC_REPO_BASE_DIR"
}

#####
## ## Get and process new docs
#####

function copy_to_debug() {
  mkdir /home/sdc/debug
  cp -r "$LOCAL_PDF_DIR_PATH"/* /home/sdc/debug/
}

function run_model_trainer() {
  echo "RUNNING MODEL_TRAINER"
  "$PYTHON_CMD" -m gamechangerml.scripts.run_model_trainer \
    -d "$LOCAL_BASE_MODEL_DIR_PATH" \
    -c "$LOCAL_CORPUS_DIR_PATH" \
    | tee "$LOCAL_JOB_LOG_PATH"
}

#####
## ## S3 ENV Vars
#####

function setup_s3_vars_and_dirs() {
  local S3_GAMECHANGER_PROD_PATH="advana-data-zone/bronze/gamechanger"
  local S3_GAMECHANGER_TEST_PATH="advana-data-zone/bronze/gamechanger"

  # data pipeline base/prod/test paths
  local S3_DATA_PIPELINE_PROD_BASE_PATH="$S3_GAMECHANGER_PROD_PATH/data-pipelines"
  local S3_DATA_PIPELINE_TEST_BASE_PATH="$S3_GAMECHANGER_TEST_PATH/data-pipelines"
  local S3_DATA_PIPELINE_PROD_PATH="$S3_DATA_PIPELINE_PROD_BASE_PATH/prod"
  local S3_DATA_PIPELINE_TEST_PATH="$S3_DATA_PIPELINE_TEST_BASE_PATH/test"

  # orchestration prod/test
  local S3_DATA_PIPELINE_PROD_ORCHESTRATION_PATH="$S3_DATA_PIPELINE_PROD_PATH/orchestration"
  local S3_DATA_PIPELINE_TEST_ORCHESTRATION_PATH="$S3_DATA_PIPELINE_TEST_PATH/orchestration"

  # prod/test repo paths
  local S3_GC_PROD_REPO_TGZ_PATH="$S3_DATA_PIPELINE_PROD_ORCHESTRATION_PATH/repo/gamechanger-repo-ds.tgz"
  local S3_GC_TEST_REPO_TGZ_PATH="$S3_DATA_PIPELINE_TEST_ORCHESTRATION_PATH/repo/gamechanger-repo-ds.tgz"

  # pdf/json  prod/test
  local S3_GC_PROD_PDF_PATH="$S3_GAMECHANGER_PROD_PATH/pdf"
  local S3_GC_PROD_JSON_PATH="$S3_GAMECHANGER_PROD_PATH/json_ds"
  local S3_GC_TEST_PDF_PATH="$S3_GAMECHANGER_TEST_PATH/test/pdf"
  local S3_GC_TEST_JSON_PATH="$S3_GAMECHANGER_TEST_PATH/test/json_ds"

  case "$SCRIPT_ENV" in
  test)
    S3_GAMECHANGER_PATH="$S3_GAMECHANGER_TEST_PATH"
    S3_DATA_PIPELINE_PATH="$S3_DATA_PIPELINE_TEST_PATH"
    S3_PIPELINE_ORCHESTRATION_PATH="$S3_DATA_PIPELINE_TEST_ORCHESTRATION_PATH"
    S3_GC_REPO_TGZ_PATH="$S3_GC_TEST_REPO_TGZ_PATH"
    S3_GC_PDF_PATH="$S3_GC_TEST_PDF_PATH"
    S3_GC_JSON_PATH="$S3_GC_TEST_JSON_PATH"
    ;;
  prod|dev)
    S3_GAMECHANGER_PATH="$S3_GAMECHANGER_PROD_PATH"
    S3_DATA_PIPELINE_PATH="$S3_DATA_PIPELINE_PROD_PATH"
    S3_PIPELINE_ORCHESTRATION_PATH="$S3_DATA_PIPELINE_PROD_ORCHESTRATION_PATH"
    S3_GC_REPO_TGZ_PATH="$S3_GC_PROD_REPO_TGZ_PATH"
    S3_GC_PDF_PATH="$S3_GC_PROD_PDF_PATH"
    S3_GC_JSON_PATH="$S3_GC_PROD_JSON_PATH"
    ;;
  *)
    echo >&2 "Must set SCRIPT_ENV = (prod|dev|test)"
    exit 2
    ;;
  esac

  # trained model paths
  MODEL_VERSION="v3"
  S3_MODEL_BASE_PATH="$S3_GAMECHANGER_PATH/models/$MODEL_VERSION"

  # log output path
  S3_PIPELINE_LOG_PATH="$S3_PIPELINE_ORCHESTRATION_PATH/logs"

}

#####
## ## S3 Fetch/Update Functions
#####

function download_corpus_from_s3() {
  $AWS_CMD s3 cp --recursive "s3://$S3_GC_JSON_PATH/" "$LOCAL_CORPUS_DIR_PATH" --include "*.json"
}

function sync_model_to_s3() {
  $AWS_CMD s3 sync "$LOCAL_BASE_MODEL_DIR_PATH/" "s3://$S3_MODEL_BASE_PATH"
}

function copy_logs_to_s3() {
  local _s3_log_name="model_trainer_$(date "+%Y-%m-%d").log"
  $AWS_CMD s3 cp "$LOCAL_JOB_LOG_PATH" "s3://$S3_PIPELINE_LOG_PATH/$_s3_log_name"
}

##### ##### #####
## ## ## ## ## ## ACTUAL EXEC FLOW
##### ##### #####

# pre-setup
if [[ "$SCRIPT_ENV" != "dev" ]]; then
  init_prod_key_tab
fi
setup_aws_and_python_exec_commands
echo_tmp_dir_locaton
setup_local_vars_and_dirs
setup_s3_vars_and_dirs

# setup repo
setup_local_repo_copy
change_into_local_repo_dir

# run trainer
download_corpus_from_s3
run_model_trainer

# update final s3 locations
sync_model_to_s3
# copy logs
copy_logs_to_s3
