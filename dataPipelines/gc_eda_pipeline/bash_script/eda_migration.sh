#!/usr/bin/env bash
set -o errexit
set -o nounset
set -o pipefail
SECONDS=0

# AWS_REGION=us-gov-west-1
# S3_GC_REPO_TGZ_PATH=advana-eda-wawf-restricted/gamechanger/projects/eda/data-pipelines/orchestration/repo/gamechanger-repo.tgz
# GC_APP_CONFIG_EXT_S3_PATH=advana-eda-wawf-restricted/gamechanger/projects/eda/data-pipelines/orchestration/repo/eda_prod.json
# GC_APP_CONFIG_NAME=eda_prod
# NUM_DATASETS_PROCESS_AT_TIME=5
# NUM_THREADS_PER_DATASET=250

AWS_REGION=us-east-1
S3_GC_REPO_TGZ_PATH=advana-data-zone/bronze/gamechanger/projects/eda/data-pipelines/orchestration/repo/gamechanger-repo.tgz
GC_APP_CONFIG_EXT_S3_PATH=advana-data-zone/bronze/gamechanger/projects/eda/data-pipelines/orchestration/repo/eda_dev.json
GC_APP_CONFIG_NAME=eda_dev
NUM_DATASETS_PROCESS_AT_TIME=5
NUM_THREADS_PER_DATASET=250

export AWS_METADATA_SERVICE_TIMEOUT=20
export AWS_METADATA_SERVICE_NUM_ATTEMPTS=40

[ -z "$AWS_REGION" ] && echo "Please provide AWS Region" && exit 2
[ -z "$S3_GC_REPO_TGZ_PATH" ] && echo "Please provide GC source code path in S3" && exit 2
[ -z "$AWS_S3_INPUT_JSON_PREFIX" ] && echo "Please provide json folder in S3" && exit 2
[ -z "$GC_APP_CONFIG_EXT_S3_PATH" ] && echo "Please provide the location of the GC App Config file location in S3" && exit 2
[ -z "$GC_APP_CONFIG_NAME" ] && echo "Please provide the location of the GC App Config file location in S3" && exit 2
[ -z "$NUM_DATASETS_PROCESS_AT_TIME" ] && echo "Please provide number of dataset  to run at a time" && exit 2
[ -z "$NUM_THREADS_PER_DATASET" ] && echo "Please provide number of threads to run at a time" && exit 2

# always set in stage params
GC_APP_CONFIG_NAME=${GC_APP_CONFIG_NAME:-eda_prod}
# Check basic params
case "$GC_APP_CONFIG_NAME" in
    eda_dev)
        echo "RUNNING IN DEV ENV"
        ;;
    eda_prod)
        echo "RUNNING IN PROD ENV"
        ;;
    *)
        echo >&2 "Must set GC_APP_CONFIG_NAME = (eda_prod|eda_dev)"
        exit 2
        ;;
    esac
#####
## ## SETUP TMP DIR
#####
function setup_tmp_dir() {
  case "$GC_APP_CONFIG_NAME" in
    eda_dev)
      LOCAL_TMP_DIR="$(mktemp -d)"
      ;;
    eda_prod)
      LOCAL_TMP_DIR="$(mktemp -d)"
      ;;
    *)
    echo >&2 "Must set GC_APP_CONFIG_NAME = (eda_prod|eda_dev)"
    exit 2
    ;;
  esac
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
    case "$GC_APP_CONFIG_NAME" in
        eda_dev)
            PYTHON_CMD="/opt/gc-venv/bin/python"
            #PYTHON_CMD="/home/centos/anaconda3/envs/eda/bin/python"
            AWS_CMD="/usr/local/bin/aws"
        ;;
        eda_prod)
            PYTHON_CMD="/opt/gc-venv-blue/bin/python"
            AWS_CMD="/usr/bin/aws"
            ;;
        *)
            echo >&2 "Must set SCRIPT_ENV = (prod|dev)"
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
    cd "$LOCAL_GC_REPO_BASE_DIR/gamechanger-data"
    export PYTHONPATH="$LOCAL_GC_REPO_BASE_DIR/gamechanger-data"
    case "$GC_APP_CONFIG_NAME" in
    eda_dev)
        source /opt/gc-venv/bin/activate
        ;;
    eda_prod)
        source /opt/gc-venv-blue/bin/activate
        ;;
    *)
        echo >&2 "Must set SCRIPT_ENV = (eda_prod|eda_dev)"
        exit 2 ;;
    esac
}
#####
## ## Run Copy App Config
#####
function copy_app_config(){
    echo "START with Copy App Config"
    export AWS_DEFAULT_REGION=$AWS_REGION
    $AWS_CMD s3 cp "s3://$GC_APP_CONFIG_EXT_S3_PATH" "$GC_APP_CONFIG_EXT_PATH"
    echo "DONE with Copy App Config"
}

function change_into_local_repo_dir() {
    cd "$LOCAL_GC_REPO_BASE_DIR"
}
#####
## Run EDA Files
#####
function eda_files() {
    echo "RUNNING Gamechanger EDA Migration"
    export PYTHONPATH=$LOCAL_TMP_DIR/app-repo/gamechanger-data
    export GC_APP_CONFIG_NAME=$GC_APP_CONFIG_NAME
    export GC_APP_CONFIG_EXT_NAME=$GC_APP_CONFIG_EXT_PATH
    cd $LOCAL_TMP_DIR/app-repo/gamechanger-data
    echo "---------------------------------------------------------------"
    "$PYTHON_CMD" -m configuration init "$GC_APP_CONFIG_NAME"
    echo "---------------------------------------------------------------"
    "$PYTHON_CMD" -m dataPipelines.gc_eda_pipeline.gc_eda_migration --aws-s3-input-json-prefix $AWS_S3_INPUT_JSON_PREFIX --number-of-datasets-to-process-at-time $NUM_DATASETS_PROCESS_AT_TIME --number-threads-per-dataset $NUM_THREADS_PER_DATASET
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
# EDA files
eda_files
duration=$SECONDS
echo "$(($duration / 60)) minutes and $(($duration % 60)) seconds elapsed."
echo "***************************** Done ****************************"
