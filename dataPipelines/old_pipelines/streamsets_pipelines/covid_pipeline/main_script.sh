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
## ## Commands to use Python and AWS
#####
function setup_aws_and_es_exec_commands() {
  case "$SCRIPT_ENV" in
  dev)
    PYTHON_CMD="/opt/gc-venv/bin/python"
    AWS_CMD="aws"
    ;;
  prod)
    PYTHON_CMD="/opt/gc-venv/bin/python"
    AWS_CMD="aws"
    ;;
  docker|local)
    PYTHON_CMD="/home/sdc/app-venv/bin/python"
    AWS_CMD="aws --endpoint-url http://localstack:4572"
    ;;
  *)
    echo >&2 "Must set SCRIPT_ENV = (prod|dev|docker|local)"
    exit 2
    ;;
  esac
  echo "Using Python: $PYTHON_CMD"
  echo "Using AWS: $AWS_CMD"
}

#####
## ## SETUP LOCAL WORK DIRECTORIES
#####
function setup_local_vars_and_dirs() {
  LOCAL_GC_REPO_BASE_DIR="$LOCAL_TMP_DIR/app-repo"
  LOCAL_GC_REPO_TGZ_PATH="$LOCAL_GC_REPO_BASE_DIR/repo.tgz"
  LOCAL_COVID_19_DIR="$LOCAL_TMP_DIR/covid19"
  mkdir -p $LOCAL_TMP_DIR/covid19/
  GC_APP_CONFIG_EXT_PATH="$LOCAL_TMP_DIR/app-conf.json"
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
  cd "$LOCAL_GC_REPO_BASE_DIR/gamechanger"
  export PYTHONPATH="$LOCAL_GC_REPO_BASE_DIR/gamechanger"
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
#####
## ## Run COVID 19 Pipeline
#####
function run_covid_19_pipeline() {
  echo "RUNNING GC COVID 19"
  export GC_APP_CONFIG_NAME="$SCRIPT_ENV"
  export GC_APP_CONFIG_EXT_NAME="$GC_APP_CONFIG_EXT_PATH"
  export OPENBLAS_NUM_THREADS=1

  "$PYTHON_CMD" -m dataPipelines.gc_covid_pipeline.covid_pipeline --staging-folder $LOCAL_COVID_19_DIR --es-index $ES_INDEX_NAME --es-alias $ES_ALIAS --s3-covd-dataset $S3_RAW_COVD19_DATASET --gc-project covid19 -p $CPU_CORES

  echo "Finish RUNNING GC COVID 19"
}

echo $LOCAL_TMP_DIR


setup_local_vars_and_dirs
setup_aws_and_es_exec_commands
setup_local_repo_copy
copy_app_config
run_covid_19_pipeline


duration=$SECONDS
echo "$(($duration / 60)) minutes and $(($duration % 60)) seconds elapsed."
echo "***************************** Done *****************************"