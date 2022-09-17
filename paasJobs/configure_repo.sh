#!/usr/bin/env bash

set -o errexit
set -o nounset
set -o pipefail
set -o noclobber

## Setting up variables to run the repo configuration ##
readonly SCRIPT_PARENT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
readonly REPO_DIR="$( cd "$SCRIPT_PARENT_DIR/../"  >/dev/null 2>&1 && pwd )"

export PYTHONPATH="$REPO_DIR"

# Check for the case that we're running this configuration in local to assign python path
DEPLOYMENT_ENV="${DEPLOYMENT_ENV:-prod}"
if [[ "${DEPLOYMENT_ENV}" != "local" ]]; then
  PYTHON_CMD="${PYTHON_CMD:-/opt/gc-venv-current/bin/python}"  # path to python executable
else
  PYTHON_CMD="${PYTHON_CMD:-python}"
fi
AWS_CMD="${AWS_CMD:-aws}"
S3_BUCKET_NAME="${S3_BUCKET_NAME:-advana-data-zone}"
APP_CONFIG_NAME="${APP_CONFIG_NAME:-$DEPLOYMENT_ENV}"
ES_CONFIG_NAME="${ES_CONFIG_NAME:-$DEPLOYMENT_ENV}"
APP_CONFIG_LOCAL_PATH="${REPO_DIR}/configuration/app-config/${APP_CONFIG_NAME}.json"
GAMECHANGERML_PKG_DIR="${GAMECHANGERML_PKG_DIR:-${REPO_DIR}/var/gamechanger-ml}"
TOPIC_MODEL_LOCAL_DIR="${GAMECHANGERML_PKG_DIR}/gamechangerml/models/topic_model_20220125163613/models"
TOPIC_MODEL_SCRIPT_LOCAL_DIR="${GAMECHANGERML_PKG_DIR}/gamechangerml/models/topic_model_20220125163613/"

# Setting up s3 path variables depending on if running in prod or running in dev/local
case $DEPLOYMENT_ENV in
  prod)
    AWS_DEFAULT_REGION="${AWS_DEFAULT_REGION:-us-gov-west-1}"
    APP_CONFIG_S3_PATH="${APP_CONFIG_S3_PATH:-s3://${S3_BUCKET_NAME}/bronze/gamechanger/configuration/app-config/prod.20210416.json}"
    TOPIC_MODEL_S3_PATH="${TOPIC_MODEL_S3_PATH:-s3://${S3_BUCKET_NAME}/bronze/gamechanger/models/topic_model/v2/topic_model_20220125163613.tar.gz}"
    TOPIC_MODEL_SCRIPT_S3_PATH="${TOPIC_MODEL_SCRIPT_S3_PATH:-s3://${S3_BUCKET_NAME}/bronze/gamechanger/models/topic_model/tfidf.py}"
    ;;
  dev | local)
    AWS_DEFAULT_REGION="${AWS_DEFAULT_REGION:-us-east-1}"
    APP_CONFIG_S3_PATH="${APP_CONFIG_S3_PATH:-s3://${S3_BUCKET_NAME}/bronze/gamechanger/configuration/app-config/dev.20220419.json}"
    TOPIC_MODEL_S3_PATH="${TOPIC_MODEL_S3_PATH:-s3://${S3_BUCKET_NAME}/bronze/gamechanger/models/topic_model/v2/topic_model_20220125163613.tar.gz}"
    TOPIC_MODEL_SCRIPT_S3_PATH="${TOPIC_MODEL_SCRIPT_S3_PATH:-s3://${S3_BUCKET_NAME}/bronze/gamechanger/models/topic_model/tfidf.py}"
    ;;
  *)
    >&2 echo "[ERROR] Incorrect DEPLOYMENT_ENV specified: $DEPLOYMENT_ENV"
    exit 1
    ;;
esac


## Defining the functions to be run in the configuration ##
function ensure_gamechangerml_is_installed() {
  # This fuction makes sure that gamechanger-ml repo is cloned/installed in GAMECHANGERML_PKG_DIR defined above
  # running the clone
  if [[ ! -d "$GAMECHANGERML_PKG_DIR" ]]; then
    >&2 echo "[INFO] Downloading gamechangerml ..."
    git clone https://github.com/dod-advana/gamechanger-ml.git "$GAMECHANGERML_PKG_DIR"
  fi
  # running the pip install
  if $PYTHON_CMD -m pip freeze | grep -qv gamechangerml ; then
    >&2 echo "[INFO] Installing gamechangerml in the user packages ..."
    $PYTHON_CMD -m pip install --no-deps -e "$GAMECHANGERML_PKG_DIR"
  fi
}


function install_app_config() {
  # This function downloads the app-config from s3 if we're not in a local environment
  if [[ "${DEPLOYMENT_ENV}" != "local" ]]; then
    if [[ -f "$APP_CONFIG_LOCAL_PATH" ]]; then
        >&2 echo "[INFO] Removing old App Config"
        rm -f "$APP_CONFIG_LOCAL_PATH"
    fi

    >&2 echo "[INFO] Fetching new App Config"
    $AWS_CMD s3 cp "$APP_CONFIG_S3_PATH" "$APP_CONFIG_LOCAL_PATH"
  fi
}

function install_topic_models() {
  # Downloads the topic model .tar file and extracts it into the gamechanger-ml repo
  if [ -d "$TOPIC_MODEL_LOCAL_DIR" ]; then
    >&2 echo "[INFO] Removing old topic model directory and contents"
    rm -rf "$TOPIC_MODEL_LOCAL_DIR"
  fi

  mkdir -p "$TOPIC_MODEL_LOCAL_DIR"

  >&2 echo "[INFO] Fetching new topic model"
  # TODO: Dynamically handle tar files that tar root directory (dealing with strip-components), or communicate with the data science team for clarity
  $AWS_CMD s3 cp "$TOPIC_MODEL_S3_PATH" - | tar -xzf - -C "$TOPIC_MODEL_LOCAL_DIR" --strip-components=1
}

function install_topic_model_script() {
  # This downloads a supplementary .py script to make sure the topic models can be imported
  mkdir -p "$TOPIC_MODEL_SCRIPT_LOCAL_DIR"

  >&2 echo "[INFO] Inserting topic model script into gamechangerml"
  $AWS_CMD s3 cp "$TOPIC_MODEL_SCRIPT_S3_PATH" "$TOPIC_MODEL_SCRIPT_LOCAL_DIR"
}

function configure_repo() {
  # Runs the configuration command to adjust gamechanger-data to the appropriate downloaded app-config
  >&2 echo "[INFO] Initializing default config files"
  >&2 echo "$PYTHON_CMD -m configuration init $DEPLOYMENT_ENV --app-config $APP_CONFIG_NAME --elasticsearch-config $ES_CONFIG_NAME"
  $PYTHON_CMD -m configuration init "$DEPLOYMENT_ENV" \
  	--app-config "$APP_CONFIG_NAME" \
  	--elasticsearch-config "$ES_CONFIG_NAME"
}

function post_checks() {
  # Checks the connections to s3/elasticsearch/neo4j/postgres
  if [[ "${DEPLOYMENT_ENV}" != "local" ]]; then
    >&2 echo "[INFO] Running post-deploy checks.../"

    >&2 echo "[INFO] Checking connections.../"
    $PYTHON_CMD -m configuration check-connections
  else
    >&2 echo "[INFO] Please manually check that the configurations are working properly."
  fi
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

## Running the configuration functions ##
install_app_config
ensure_gamechangerml_is_installed
install_topic_models
install_topic_model_script
configure_repo
post_checks


>&2 cat <<EOF

#####                                   #####
#####      Configuration Completed      #####
#####                                   #####

EOF

