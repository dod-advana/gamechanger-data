#!/usr/bin/env bash

#####
## ## SETUP TMP DIR
#####
function setup_tmp_dir() {
  if [[ $SCRIPT_ENV="prod" ]]; then
    LOCAL_TMP_DIR=$(mktemp -d)
  else
    LOCAL_TMP_DIR=$(mktemp -d)
  fi
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

function kinit_command() {
  if [ "$SCRIPT_ENV" = "prod" ]; then
    kinit -k -t /etc/security/keytabs/streamsets.keytab "${KRB_NAME}"
  fi
}

#####
## ## SETUP LOCAL WORK DIRECTORIES
#####

function setup_local_vars_and_dirs() {

  if [[ "$SCRIPT_ENV" == "dev" ]]; then
    LOCAL_GC_REPO_BASE_DIR="/tmp/test/repo"
    #LOCAL_GC_REPO_BASE_DIR="$LOCAL_TMP_DIR/app-repo"
  else
    LOCAL_GC_REPO_BASE_DIR="$LOCAL_TMP_DIR/app-repo"
	echo $LOCAL_GC_REPO_BASE_DIR
  fi

  LOCAL_GC_REPO_TGZ_PATH="$LOCAL_GC_REPO_BASE_DIR/repo.tgz"
  LOCAL_CORPUS_DIR_PATH="$LOCAL_TMP_DIR/corpus"
  LOCAL_BASE_MODEL_DIR_PATH="$LOCAL_TMP_DIR/models"

  mkdir -p "$LOCAL_GC_REPO_BASE_DIR"
  mkdir -p "$LOCAL_CORPUS_DIR_PATH"
  mkdir -p "$LOCAL_BASE_MODEL_DIR_PATH"

}

#####
## ## SETUP COMMANDS & DIRS
#####


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
    AWS_CMD="aws"
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
      $AWS_CMD s3 cp "s3://$S3_GC_REPO_TGZ_PATH" "$LOCAL_GC_REPO_TGZ_PATH"
      tar -xzf "$LOCAL_GC_REPO_TGZ_PATH" -C "$LOCAL_GC_REPO_BASE_DIR"
      return 0
    fi
  fi
  if [[ "$SCRIPT_ENV" == "prod" ]]; then
    if [[ $(ls -A "$LOCAL_GC_REPO_BASE_DIR") ]]; then
      echo "LOCAL REPO dir should be mounted at: $LOCAL_GC_REPO_BASE_DIR"
      return 0
	else
      echo &>2 "LOCAL REPO dir appears empty: $LOCAL_GC_REPO_BASE_DIR"
      $AWS_CMD s3 cp "s3://$S3_GC_REPO_TGZ_PATH" "$LOCAL_GC_REPO_TGZ_PATH"
      tar -xzf "$LOCAL_GC_REPO_TGZ_PATH" -C "$LOCAL_GC_REPO_BASE_DIR"
      return 0
    fi
  fi
}

function change_into_local_repo_dir() {
  echo "CHANGING DIRECTORIES"
  echo $LOCAL_GC_REPO_BASE_DIR
  cd "$LOCAL_GC_REPO_BASE_DIR/gamechanger"
  echo $(ls /run  -ltr)
  echo $(pwd)
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
  "$PYTHON_CMD" -m gamechangerml.scripts.run_train_models --modeldest "$LOCAL_BASE_MODEL_DIR_PATH" --corpus "$LOCAL_CORPUS_DIR_PATH"
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
  local S3_DATA_PIPELINE_PROD_PATH="$S3_DATA_PIPELINE_PROD_BASE_PATH"
  local S3_DATA_PIPELINE_TEST_PATH="$S3_DATA_PIPELINE_TEST_BASE_PATH"

  # orchestration prod/test
  local S3_DATA_PIPELINE_PROD_ORCHESTRATION_PATH="$S3_DATA_PIPELINE_PROD_PATH/orchestration"
  local S3_DATA_PIPELINE_TEST_ORCHESTRATION_PATH="$S3_DATA_PIPELINE_TEST_PATH/orchestration"

  # prod/test repo paths
  local S3_GC_PROD_REPO_TGZ_PATH="$S3_DATA_PIPELINE_PROD_ORCHESTRATION_PATH/repo/gamechanger-repo.tgz"
  local S3_GC_TEST_REPO_TGZ_PATH="$S3_DATA_PIPELINE_TEST_ORCHESTRATION_PATH/repo/gamechanger-repo.tgz"

  # pdf/json  prod/test
  local S3_GC_PROD_PDF_PATH="$S3_GAMECHANGER_PROD_PATH/pdf_model"
  local S3_GC_PROD_JSON_PATH="$S3_GAMECHANGER_PROD_PATH/json_model"
  local S3_GC_TEST_PDF_PATH="$S3_GAMECHANGER_TEST_PATH/test/pdf_model"
  local S3_GC_TEST_JSON_PATH="$S3_GAMECHANGER_TEST_PATH/test/json_model"

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
  esac

  # trained model paths
  S3_MODEL_BASE_PATH="$S3_GAMECHANGER_PATH/projects/"


}

#####
## ## S3 Fetch/Update Functions
#####


function download_corpus_from_s3() {
  number_of_files=$($AWS_CMD s3 ls s3://advana-data-zone/bronze/gamechanger/projects/$PROJECT/json | wc -l)
  if [[ $number_of_files -eq 0 ]]; then
    echo "no files in directory."
	exit 1
  else
    $AWS_CMD s3 cp --recursive "s3://advana-data-zone/bronze/gamechanger/projects/$PROJECT/json" "$LOCAL_CORPUS_DIR_PATH" --include "*.json"
  fi
}

function sync_model_to_s3() {
  MODEL_PATH=$(find "$LOCAL_BASE_MODEL_DIR_PATH/"  -mindepth 1 -maxdepth 1 -type d)
  MODEL_NAME=$(basename $MODEL_PATH)
  $AWS_CMD s3 rm --recursive "s3://advana-data-zone/bronze/gamechanger/projects/$PROJECT/models/$MODEL_VERSION/$MODEL_NAME"
  $AWS_CMD s3 cp --recursive "$LOCAL_BASE_MODEL_DIR_PATH/$MODEL_NAME" "s3://advana-data-zone/bronze/gamechanger/projects/$PROJECT/models/$MODEL_VERSION/$MODEL_NAME"
}

##### ##### #####
## ## ## ## ## ## ACTUAL EXEC FLOW
##### ##### #####

# pre-setup

kinit_command
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
