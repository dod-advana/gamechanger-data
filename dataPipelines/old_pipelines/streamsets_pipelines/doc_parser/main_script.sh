#!/usr/bin/env bash

set -o errexit
set -o nounset
set -o pipefail

SECONDS=0

# always set in stage params
SCRIPT_ENV=${SCRIPT_ENV:-dev}

# Check basic params
case "$SCRIPT_ENV" in
dev)
  echo "RUNNING IN DEV ENV"
  ;;
prod)
  echo "RUNNING IN PROD ENV"
  ;;
docker)
  echo "RUNNING IN DOCKER ENV"
  ;;
*)
  echo >&2 "Must set SCRIPT_ENV = (prod|dev|docker)"
  exit 2
  ;;
esac

#####
## ## SETUP TMP DIR
#####
function setup_tmp_dir() {
  LOCAL_TMP_DIR="/var/$(mktemp -d)"
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
}
trap cleanup_hooks EXIT

#####
## ## SETUP LOCAL WORK DIRECTORIES
#####
function setup_local_vars_and_dirs() {
  LOCAL_GC_REPO_BASE_DIR="$LOCAL_TMP_DIR/app-repo"
  LOCAL_GC_REPO_TGZ_PATH="$LOCAL_GC_REPO_BASE_DIR/repo.tgz"
  LOCAL_GC_DIR="$LOCAL_TMP_DIR/gc"
  mkdir -p "$LOCAL_GC_REPO_BASE_DIR"
  mkdir -p "$LOCAL_GC_DIR"
  GC_APP_CONFIG_EXT_PATH="$LOCAL_TMP_DIR/app-conf.json"
}

#####
## ## Commands to use Python and AWS
#####
function setup_aws_and_python_exec_commands() {
  case "$SCRIPT_ENV" in
  dev)
    PYTHON_CMD="/opt/gc-venv/bin/python"
    AWS_CMD="aws"
    ;;
  prod)
    PYTHON_CMD="/opt/gc-venv/bin/python"
    AWS_CMD="aws"
    ;;
  docker)
    PYTHON_CMD="/home/sdc/app-venv/bin/python"
    AWS_CMD="aws --endpoint-url http://localstack:4572"
    ;;
  *)
    echo >&2 "Must set SCRIPT_ENV = (prod|dev|test)"
    exit 2
    ;;
  esac
  echo "Using Python: $PYTHON_CMD"
  echo "Using AWS: $AWS_CMD"
}

#####
## ## S3 ENV Vars
#####
function setup_s3_vars_and_dirs() {
  echo "S3 GC Path Orchestartion App $S3_GC_REPO_TGZ_PATH"
}

#####
## ## Copy Gamechanger code from S3 to locally
#####
function setup_local_repo_copy() {
  echo "FETCHING REPO"
  export AWS_DEFAULT_REGION=$AWS_REGION
  $AWS_CMD s3 cp "s3://$S3_GC_REPO_TGZ_PATH" "$LOCAL_GC_REPO_TGZ_PATH"
  tar -xvzf "$LOCAL_GC_REPO_TGZ_PATH" -C "$LOCAL_GC_REPO_BASE_DIR"

  # init repo config
  cd "$LOCAL_TMP_DIR/app-repo/gamechanger"
  export PYTHONPATH="$LOCAL_TMP_DIR/app-repo/gamechanger"
  "$PYTHON_CMD" -m configuration init "$SCRIPT_ENV"
}

#####
## ## Run Copy App Config
#####
function copy_app_config(){
  echo "FETCHING APP Config"
  export AWS_DEFAULT_REGION=$AWS_REGION
  $AWS_CMD s3 cp "s3://$GC_APP_CONFIG_EXT_S3_PATH" "$GC_APP_CONFIG_EXT_PATH"
}

function change_into_local_repo_dir() {
  cd "$LOCAL_GC_REPO_BASE_DIR"
}

#####
## ## Run Gamechanger Symphony
#####
function gamechanger_symphony() {
echo "RUNNING Gamechanger Symphony"
	export PYTHONPATH=$LOCAL_TMP_DIR/app-repo/gamechanger
    export GC_APP_CONFIG_NAME=$SCRIPT_ENV
    export GC_APP_CONFIG_EXT_NAME=$GC_APP_CONFIG_EXT_PATH
  	cd $LOCAL_TMP_DIR/app-repo/gamechanger
    "$PYTHON_CMD" -m dataPipelines.gc_symphony_pipeline.gc_pipeline --staging-folder $LOCAL_GC_DIR --aws-s3-json-prefix $AWS_S3_JSON_PREFIX --aws-s3-pdf-prefix $AWS_S3_PDF_PREFIX --es-index $ES_INDEX_NAME --es-alias $ES_ALIAS -p $CPU_CORES


}
echo "***************************** Start *****************************"
setup_aws_and_python_exec_commands
echo_tmp_dir_locaton
setup_local_vars_and_dirs
setup_s3_vars_and_dirs

# setup repo
copy_app_config
setup_local_repo_copy
change_into_local_repo_dir

# Gamechanger Symphony
gamechanger_symphony

duration=$SECONDS
echo "$(($duration / 60)) minutes and $(($duration % 60)) seconds elapsed."
echo "***************************** Done *****************************"