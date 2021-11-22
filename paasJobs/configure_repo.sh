#!/usr/bin/env bash

set -o errexit
set -o nounset
set -o pipefail
set -o noclobber

readonly SCRIPT_PARENT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
readonly REPO_DIR="$( cd "$SCRIPT_PARENT_DIR/../"  >/dev/null 2>&1 && pwd )"

export PYTHONPATH="$REPO_DIR"

SCRIPT_ENV="${SCRIPT_ENV:-prod}"
AWS_CMD="${AWS_CMD:-aws}"
PYTHON_CMD="${PYTHON_CMD:-/opt/gc-venv-current/bin/python}"
S3_BUCKET_NAME="${S3_BUCKET_NAME:-advana-data-zone}"
APP_CONFIG_NAME="${APP_CONFIG_NAME:-$SCRIPT_ENV}"
ES_CONFIG_NAME="${ES_CONFIG_NAME:-$SCRIPT_ENV}"
APP_CONFIG_LOCAL_PATH="${REPO_DIR}/configuration/app-config/${APP_CONFIG_NAME}.json"
GAMECHANGERML_PKG_DIR="${GAMECHANGERML_PKG_DIR:-${REPO_DIR}/var/gamechanger-ml}"
TOPIC_MODEL_LOCAL_DIR="${GAMECHANGERML_PKG_DIR}/gamechangerml/models/topic_models/models/"


case $SCRIPT_ENV in
  prod)
    AWS_DEFAULT_REGION="${AWS_DEFAULT_REGION:-us-gov-west-1}"
    APP_CONFIG_S3_PATH="${APP_CONFIG_S3_PATH:-s3://${S3_BUCKET_NAME}/bronze/gamechanger/configuration/app-config/prod.20210416.json}"
    TOPIC_MODEL_S3_PATH="${TOPIC_MODEL_S3_PATH:-s3://${S3_BUCKET_NAME}/bronze/gamechanger/models/topic_model/v1/20210208.tar.gz}"
    ;;
  dev)
    AWS_DEFAULT_REGION="${AWS_DEFAULT_REGION:-us-east-1}"
    APP_CONFIG_S3_PATH="${APP_CONFIG_S3_PATH:-s3://${S3_BUCKET_NAME}/bronze/gamechanger/configuration/app-config/dev.20211118.json}"
    TOPIC_MODEL_S3_PATH="${TOPIC_MODEL_S3_PATH:-s3://${S3_BUCKET_NAME}/bronze/gamechanger/models/topic_model/v1/20210208.tar.gz}"
    ;;
  local)
    >&2 echo "[INFO] LOCAL SETUP: Skipping app config install and topic model install."
    >&2 echo "[INFO] Please copy topic model over manually."
    ;;
  *)
    >&2 echo "[ERROR] Incorrect SCRIPT_ENV specified: $SCRIPT_ENV"
    exit 1
    ;;
esac


function ensure_gamechangerml_is_installed() {
  if [[ ! -d "$GAMECHANGERML_PKG_DIR" ]]; then
    >&2 echo "[INFO] Downloading gamechangerml ..."
    git clone https://github.com/dod-advana/gamechanger-ml.git "$GAMECHANGERML_PKG_DIR"
  fi

  if $PYTHON_CMD -m pip freeze | grep -qv gamechangerml ; then
    >&2 echo "[INFO] Installing gamechangerml in the user packages ..."
    $PYTHON_CMD -m pip install --no-deps -e "$GAMECHANGERML_PKG_DIR"
  fi
}


function install_app_config() {
  if [[ "${SCRIPT_ENV}" != "local" ]]; then
    if [[ -f "$APP_CONFIG_LOCAL_PATH" ]]; then
        >&2 echo "[INFO] Removing old App Config"
        rm -f "$APP_CONFIG_LOCAL_PATH"
    fi

    >&2 echo "[INFO] Fetching new App Config"
    $AWS_CMD s3 cp "$APP_CONFIG_S3_PATH" "$APP_CONFIG_LOCAL_PATH"
  fi
}

function install_topic_models() {
   if [[ "${SCRIPT_ENV}" != "local" ]]; then
      if [ -d "$TOPIC_MODEL_LOCAL_DIR" ]; then
        >&2 echo "[INFO] Removing old topic model directory and contents"
        rm -rf "$TOPIC_MODEL_LOCAL_DIR"
      fi

      mkdir -p "$TOPIC_MODEL_LOCAL_DIR"

      >&2 echo "[INFO] Fetching new topic model"
      $AWS_CMD s3 cp "$TOPIC_MODEL_S3_PATH" - | tar -xzf - -C "$TOPIC_MODEL_LOCAL_DIR"
   fi
}

function configure_repo() {
  >&2 echo "[INFO] Initializing default config files"
  >&2 echo "$PYTHON_CMD -m configuration init $SCRIPT_ENV --app-config $APP_CONFIG_NAME --elasticsearch-config $ES_CONFIG_NAME"
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
ensure_gamechangerml_is_installed
install_topic_models
configure_repo
post_checks


>&2 cat <<EOF

#####                                   #####
#####      Configuration Completed      #####
#####                                   #####

EOF

