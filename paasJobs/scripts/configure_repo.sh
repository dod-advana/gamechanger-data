#!/usr/bin/env bash

set -o errexit
set -o nounset
set -o pipefail
set -o noclobber

readonly SCRIPT_PARENT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
readonly REPO_DIR="$( cd "$SCRIPT_PARENT_DIR/../../"  >/dev/null 2>&1 && pwd )"

export PYTHONPATH="$REPO_DIR"

AWS_DEFAULT_REGION="${AWS_DEFAULT_REGION:-us-gov-west-1}"
AWS_CMD="${AWS_CMD:-aws}"
PYTHON_CMD="${PYTHON_CMD:-/opt/gc-venv-current/bin/python}"
SCRIPT_ENV="${SCRIPT_ENV:-prod}"

S3_BUCKET_NAME="${S3_BUCKET_NAME:-advana-raw-zone}"
APP_CONFIG_S3_PATH="${APP_CONFIG_S3_PATH:-s3://${S3_BUCKET_NAME}/gamechanger/configuration/app-config/prod.20210416.json}"

APP_CONFIG_NAME="${APP_CONFIG_NAME:-$SCRIPT_ENV}"
ES_CONFIG_NAME="${ES_CONFIG_NAME:-$SCRIPT_ENV}"

APP_CONFIG_LOCAL_PATH="${REPO_DIR}/configuration/app-config/${APP_CONFIG_NAME}.json"
TOPIC_MODEL_S3_PREFIX="${TOPIC_MODEL_S3_PATH:-s3://${S3_BUCKET_NAME}/gamechanger/configuration/topic_models/models_20210428/}"
TOPIC_MODEL_LOCAL_DIR="${REPO_DIR}/dataScience/models/topic_models/models/"


function install_app_config() {
  if [[ -f "$APP_CONFIG_LOCAL_PATH" ]]; then
    >&2 echo "[INFO] Removing old App Config"
    rm -f "$APP_CONFIG_LOCAL_PATH"
  fi

  >&2 echo "[INFO] Fetching new App Config"
  $AWS_CMD s3 cp "$APP_CONFIG_S3_PATH" "$APP_CONFIG_LOCAL_PATH"
}

function install_topic_models() {
  if [ -d "$TOPIC_MODEL_LOCAL_DIR" ]; then
    >&2 echo "[INFO] Removing old topic model directory and contents"
    rm -rf "$TOPIC_MODEL_LOCAL_DIR"
  fi

  mkdir -p "$TOPIC_MODEL_LOCAL_DIR"

  >&2 echo "[INFO] Fetching new topic model"
  $AWS_CMD s3 cp --recursive "$TOPIC_MODEL_S3_PREFIX" "$TOPIC_MODEL_LOCAL_DIR"
}

function configure_repo() {
  >&2 echo "[INFO] Initializing default config files"
  $PYTHON_CMD -m configuration init "$SCRIPT_ENV" \
  	--app-config "$APP_CONFIG_NAME" \
  	--elasticsearch-config "$ES_CONFIG_NAME"
}

function post_checks() {
  >&2 echo "[INFO] Running post-deploy checks.../"

  >&2 echo "[INFO] Checking connections.../"
  $PYTHON_CMD -m configuration check-connections
}

if [[ "${CHECK_ONLY:-no}" == "yes" ]]; then
    post_checks
    exit 0
fi

>&2 cat <<EOF

#####                                   #####
#####          Configuring Repo         #####
#####                                   #####

EOF

install_app_config
install_topic_models
configure_repo
post_checks


>&2 cat <<EOF

#####                                   #####
#####      Configuration Completed      #####
#####                                   #####

EOF

