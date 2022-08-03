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
docker|local)
  echo "RUNNING IN DOCKER/LOCAL ENV"
  ;;
*)
  echo >&2 "Must set SCRIPT_ENV = (prod|dev|docker|local)"
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
  LOCAL_TMP_DIR_GC_INDEX="$LOCAL_TMP_DIR/gamechanger.json"
  echo "LOCAL_TMP_DIR_GC_INDEX: $LOCAL_TMP_DIR_GC_INDEX"
  LOCAL_JSON_DIR_PATH="$LOCAL_TMP_DIR/parser_out"
  mkdir -p "$LOCAL_GC_REPO_BASE_DIR"
  mkdir -p "$LOCAL_JSON_DIR_PATH"
  GC_APP_CONFIG_EXT_PATH="$LOCAL_TMP_DIR/app-conf.json"
}


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
## ## Copy Gamechanger code from S3 to locally
#####
function setup_local_repo_copy() {
  echo "FETCHING REPO"
  export AWS_DEFAULT_REGION=$AWS_REGION
  echo $AWS_CMD s3 cp "s3://$S3_GC_REPO_TGZ_PATH" "$LOCAL_GC_REPO_TGZ_PATH"
  $AWS_CMD s3 cp "s3://$S3_GC_REPO_TGZ_PATH" "$LOCAL_GC_REPO_TGZ_PATH"
  tar -xvzf "$LOCAL_GC_REPO_TGZ_PATH" -C "$LOCAL_GC_REPO_BASE_DIR"

   # init repo config
  cd "$LOCAL_GC_REPO_BASE_DIR/gamechanger"
  export PYTHONPATH="$LOCAL_GC_REPO_BASE_DIR/gamechanger"
  "$PYTHON_CMD" -m configuration init "$SCRIPT_ENV"
}


#####
## ## Copy Gamechanger JSONs from S3 to locally
#####
function copy_s3_json_to_local() {
  echo "FETCHING PDF FILES"
  export AWS_DEFAULT_REGION=$AWS_REGION
  $AWS_CMD s3 cp "s3://$S3_GC_JSON_PATH" $LOCAL_JSON_DIR_PATH --recursive --include "*.json"
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
## ## Elasticsearch Index Update Vars/Functions
#####
function update_es_index() {
  echo "RUNNING Elasticsearch Indexer"
  export GC_APP_CONFIG_EXT_NAME=$GC_APP_CONFIG_EXT_PATH
 # Check basic params
  case "$SCRIPT_ENV" in
  dev|prod|docker|local)
   "$PYTHON_CMD" -m dataPipelines.gc_elasticsearch_publisher run -i "${INDEX_NAME}" -a ${ES_ALIAS} -d "$LOCAL_JSON_DIR_PATH"
    ;;
  *)
    echo >&2 "Must set SCRIPT_ENV = (prod|dev|docker|local)"
    exit 2
    ;;
  esac

  echo "Finish Elasticsearch Indexer"
}



####
echo "***************************** Start *****************************"

setup_local_vars_and_dirs
setup_aws_and_es_exec_commands
setup_local_repo_copy
copy_s3_json_to_local
copy_app_config
update_es_index

duration=$SECONDS
echo "$(($duration / 60)) minutes and $(($duration % 60)) seconds elapsed."
echo "***************************** Done *****************************"