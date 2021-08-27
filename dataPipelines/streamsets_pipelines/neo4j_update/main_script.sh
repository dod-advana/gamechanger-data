#!/usr/bin/env bash

set -o errexit
set -o nounset
set -o pipefail

# always set in stage params
SCRIPT_ENV=${SCRIPT_ENV:-dev}

# Check basic params
case "$SCRIPT_ENV" in
prod)
  echo "RUNNING IN PROD ENV"
  ;;
dev|local)
  echo "RUNNING IN LOCAL_DEV ENV"
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
trap cleanup_hooks EXIT

#####
## ## SETUP COMMANDS & LOCAL WORK DIRECTORIES
#####

function setup_aws_and_python_exec_commands() {

  case "$SCRIPT_ENV" in
  prod)
    export AWS_DEFAULT_REGION="us-gov-west-1"
    PYTHON_CMD="/opt/gc-venv/bin/python"
    AWS_CMD="aws"
    ;;
  dev|local)
    export AWS_DEFAULT_REGION="us-east-1"
    PYTHON_CMD="/home/sdc/app-venv/bin/python"
    AWS_CMD="aws --endpoint-url http://s3-server:9000"
    ;;
  *)
    echo >&2 "Must set SCRIPT_ENV = (prod|dev|local)"
    exit 2
    ;;
  esac

}

function _setup_local_repo_copy() {

  echo "FETCHING REPO"
  echo $AWS_CMD s3 cp "s3://$S3_GC_REPO_TGZ_PATH" "$LOCAL_GC_REPO_TGZ_PATH"
  $AWS_CMD s3 cp "s3://$S3_GC_REPO_TGZ_PATH" "$LOCAL_GC_REPO_TGZ_PATH"
  tar -xvzf "$LOCAL_GC_REPO_TGZ_PATH" -C "$LOCAL_GC_REPO_BASE_DIR"

}

function setup_local_vars_and_dirs() {

  case "$SCRIPT_ENV" in
  prod)
    LOCAL_PDF_DIR_PATH="$LOCAL_TMP_DIR/pdf"
    LOCAL_JSON_DIR_PATH="$LOCAL_TMP_DIR/json"
    LOCAL_GC_REPO_BASE_DIR="$LOCAL_TMP_DIR/app-repo"
    LOCAL_GC_REPO_TGZ_PATH="$LOCAL_GC_REPO_BASE_DIR/repo.tgz"

    mkdir -p "$LOCAL_GC_REPO_BASE_DIR"
    _setup_local_repo_copy
    ;;
  dev|local)
    LOCAL_GC_REPO_BASE_DIR="/repo"
    ;;
  *)
    echo >&2 "Must set SCRIPT_ENV = (prod|dev|local)"
    exit 2
    ;;
  esac

  LOCAL_PDF_DIR_PATH="$LOCAL_TMP_DIR/pdf"
  LOCAL_JSON_DIR_PATH="$LOCAL_TMP_DIR/json"
  mkdir -p "$LOCAL_PDF_DIR_PATH"
  mkdir -p "$LOCAL_JSON_DIR_PATH"
}

function change_into_local_repo_dir() {
  cd "$LOCAL_GC_REPO_BASE_DIR"
}

function configure_repo() {
  $PYTHON_CMD -m configuration init "$SCRIPT_ENV"
  $PYTHON_CMD -m configuration check-connections
}

#####
## ## S3 ENV Vars
#####

function setup_s3_vars_and_dirs() {
  local S3_GAMECHANGER_PROD_PATH="advana-data-zone/gamechanger"
  local S3_GAMECHANGER_TEST_PATH="advana-data-zone/gamechanger"

  # data pipeline base/prod/test paths
  local S3_DATA_PIPELINE_PROD_BASE_PATH="$S3_GAMECHANGER_PROD_PATH/data-pipelines"
  local S3_DATA_PIPELINE_TEST_BASE_PATH="$S3_GAMECHANGER_TEST_PATH/data-pipelines"
  local S3_DATA_PIPELINE_PROD_PATH="$S3_DATA_PIPELINE_PROD_BASE_PATH/prod"
  local S3_DATA_PIPELINE_TEST_PATH="$S3_DATA_PIPELINE_TEST_BASE_PATH/test"

  # orchestration prod/test
  local S3_DATA_PIPELINE_PROD_ORCHESTRATION_PATH="$S3_DATA_PIPELINE_PROD_PATH/orchestration"
  local S3_DATA_PIPELINE_TEST_ORCHESTRATION_PATH="$S3_DATA_PIPELINE_TEST_PATH/orchestration"

  # prod/test repo paths
  local S3_GC_PROD_REPO_TGZ_PATH="$REPO_TGZ_BASE_PATH/$REPO_TGZ_NAME"
  local S3_GC_TEST_REPO_TGZ_PATH="$REPO_TGZ_BASE_PATH/$REPO_TGZ_NAME"

  # pdf/json  prod/test
  local S3_GC_PROD_PDF_PATH="$S3_GAMECHANGER_PROD_PATH/pdf"
  local S3_GC_PROD_JSON_PATH="$S3_GAMECHANGER_PROD_PATH/json"
  local S3_GC_TEST_PDF_PATH="$S3_GAMECHANGER_TEST_PATH/test/pdf"
  local S3_GC_TEST_JSON_PATH="$S3_GAMECHANGER_TEST_PATH/test/json"

  case "$SCRIPT_ENV" in
  test)
    S3_GAMECHANGER_PATH="$S3_GAMECHANGER_TEST_PATH"
    S3_DATA_PIPELINE_PATH="$S3_DATA_PIPELINE_TEST_PATH"
    S3_PIPELINE_ORCHESTRATION_PATH="$S3_DATA_PIPELINE_TEST_ORCHESTRATION_PATH"
    S3_GC_REPO_TGZ_PATH="$S3_GC_TEST_REPO_TGZ_PATH"
    S3_GC_PDF_PATH="$S3_GC_TEST_PDF_PATH"
    S3_GC_JSON_PATH="$S3_GC_TEST_JSON_PATH"
    ;;
  prod)
    S3_GAMECHANGER_PATH="$S3_GAMECHANGER_PROD_PATH"
    S3_DATA_PIPELINE_PATH="$S3_DATA_PIPELINE_PROD_PATH"
    S3_PIPELINE_ORCHESTRATION_PATH="$S3_DATA_PIPELINE_PROD_ORCHESTRATION_PATH"
    S3_GC_REPO_TGZ_PATH="$S3_GC_PROD_REPO_TGZ_PATH"
    S3_GC_PDF_PATH="$S3_GC_PROD_PDF_PATH"
    S3_GC_JSON_PATH="$S3_GC_PROD_JSON_PATH"
    ;;
  dev|local)
    S3_GAMECHANGER_PATH="$S3_GAMECHANGER_TEST_PATH"
    S3_DATA_PIPELINE_PATH="$S3_DATA_PIPELINE_TEST_PATH"
    S3_PIPELINE_ORCHESTRATION_PATH="$S3_DATA_PIPELINE_TEST_ORCHESTRATION_PATH"
    S3_GC_REPO_TGZ_PATH="$S3_GC_TEST_REPO_TGZ_PATH"
    S3_GC_PDF_PATH="$S3_GC_TEST_PDF_PATH"
    S3_GC_JSON_PATH="$S3_GC_TEST_JSON_PATH"
    ;;
  *)
    echo >&2 "Must set SCRIPT_ENV = (prod|dev|test)"
    exit 2
    ;;
  esac

}
#####
## ## Copy Generated JSONS to S3
#####
function copy_s3_json_to_local() {
  #export AWS_DEFAULT_REGION=$AWS_REGION
  echo Downloading JSON
  $AWS_CMD s3 cp "s3://$S3_GC_JSON_PATH" "$LOCAL_JSON_DIR_PATH" --recursive --quiet --include "*.json"
}

function run_neo4j_publisher() {
  echo "RUNNING NEO4J"
  $PYTHON_CMD -m dataPipelines.gc_neo4j_publisher run --clear --source "$LOCAL_JSON_DIR_PATH"
}

##### ##### #####
## ## ## ## ## ## ACTUAL EXEC FLOW
##### ##### #####

setup_aws_and_python_exec_commands
echo_tmp_dir_locaton
setup_s3_vars_and_dirs
setup_local_vars_and_dirs

change_into_local_repo_dir
configure_repo
copy_s3_json_to_local

run_neo4j_publisher