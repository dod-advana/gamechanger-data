#!/usr/bin/env bash
set -o errexit
set -o nounset
set -o pipefail
set -o xtrace

readonly SCRIPT_PARENT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
readonly REPO_DIR="$( cd "$SCRIPT_PARENT_DIR/../../../"  >/dev/null 2>&1 && pwd )"
readonly MLAPP_VENV_DIR="${MLAPP_VENV_DIR:-/opt/app-root/venv}"
readonly DS_SETUP_PATH="${REPO_DIR}/gamechangerml/setup_env.sh"

ENV_TYPE="${ENV_TYPE:+${ENV_TYPE^^}}"
DOWNLOAD_DEP="${DOWNLOAD_DEP:+${DOWNLOAD_DEP,,}}"
CONTAINER_RELOAD="${CONTAINER_RELOAD:+${CONTAINER_RELOAD,,}}"

[[ -z "${DOWNLOAD_DEP:-}" ]] && {
  >&2 echo "[WARNING] No DOWNLOAD_DEP specified, setting to 'false' ..."
  DOWNLOAD_DEP="false"
}

case "${DOWNLOAD_DEP}" in
  true|false)
    export DOWNLOAD_DEP
    ;;
  *)
    >&2 echo "[ERROR] Invalid DOWNLOAD_DEP specified: '$DOWNLOAD_DEP'"
    exit 1
    ;;
esac

[[ -z "${ENV_TYPE:-}" ]] && {
  >&2 echo "[WARNING] No ENV_TYPE specified, setting to 'PROD' ..."
  ENV_TYPE="PROD"
}
export ENV_TYPE

[[ -z "${CONTAINER_RELOAD:-}" ]] && {
  >&2 echo "[WARNING] No CONTAINER_RELOAD specified, setting to 'false' ..."
  CONTAINER_RELOAD="false"
}
export CONTAINER_RELOAD

function download_dependencies() {
    [[ "${DOWNLOAD_DEP}" == "true" ]] && {
      echo "[INFO] Attempting to download models from S3 ..."
      echo "[INFO] GC_ML_API_MODEL_NAME=${GC_ML_API_MODEL_NAME:-[DEFAULT]}"
      echo "[INFO] Attempting to download transformer cache and sentence index from S3 ..."
      source "${REPO_DIR}/gamechangerml/scripts/download_dependencies.sh"
    } || {
      echo "[INFO] Skipping model download"
    }
}

function activate_venv() {
  set +o xtrace
  
  if [[ ! -f "${MLAPP_VENV_DIR}/bin/activate" ]]; then
    >&2 echo "[WARNING] No venv detected at ${MLAPP_VENV_DIR}; using current python env ..."
  else
    echo "[INFO] Activating venv at ${MLAPP_VENV_DIR} ..."
    source ${MLAPP_VENV_DIR}/bin/activate
  fi

  # if gamechangerml wasn't installed as module in the venv, just alter pythonpath
  if ! (pip freeze | grep -q gamechangerml); then
    >&2 echo "[WARNING] gamechangerml package not found, setting PYTHONPATH to repo root"
    export PYTHONPATH="${PYTHONPATH:-}${PYTHONPATH:+:}${REPO_DIR}"
  fi
  set -o xtrace
}

function start_gunicorn() {
  # no return from this function. Don't set traps, dont add logic after calling it..
  #  ... gunicorn will replace shell process
  echo "[INFO] Starting gunicorn workers for the API ..."
  exec gunicorn "$@"
}

function start_uvicorn() {
  # no return from this function. Don't set traps, dont add logic after calling it..
  #  ... uvicorn will replace shell process
  echo "[INFO] Starting uvicorn workers for the API ..."
  exec uvicorn "$@"
}

function start_env_prod() {
  source "${DS_SETUP_PATH}"
  activate_venv
  download_dependencies
  start_gunicorn gamechangerml.api.fastapi.mlapp:app \
    --bind 0.0.0.0:5000 \
    --workers 1 \
    --graceful-timeout 900 \
    --timeout 1200 \
    -k uvicorn.workers.UvicornWorker \
    --log-level debug
}

function start_env_dev() {
  source "${DS_SETUP_PATH}"
  activate_venv
  download_dependencies
  if [[ "${CONTAINER_RELOAD}" == "true" ]]; then
    start_uvicorn gamechangerml.api.fastapi.mlapp:app \
      --host 0.0.0.0 \
      --port 5000 \
      --workers 1 \
      --log-level debug \
      --timeout-keep-alive 240 \
      --reload
  else
    start_gunicorn gamechangerml.api.fastapi.mlapp:app \
        --bind 0.0.0.0:5000 \
        --workers 1 \
        --graceful-timeout 1000 \
        --timeout 1200 \
        --keep-alive 30 \
        --reload \
        -k uvicorn.workers.UvicornWorker \
        --log-level debug
  fi
}

function start_env_devlocal() {
  source "${DS_SETUP_PATH}"
  activate_venv
  download_dependencies
  start_gunicorn gamechangerml.api.fastapi.mlapp:app \
      --bind 0.0.0.0:5000 \
      --workers 1 \
      --graceful-timeout 900 \
      --timeout 1600 \
      -k uvicorn.workers.UvicornWorker \
      --log-level debug \
      --reload
}

function start_env_k8s_dev() {
  start_env_dev
}

function start_env_k8s_test() {
  source "${DS_SETUP_PATH}"
  activate_venv
  download_dependencies
  start_gunicorn gamechangerml.api.fastapi.mlapp:app \
      --bind 0.0.0.0:5000 \
      --workers 1 \
      --graceful-timeout 900 \
      --timeout 1200 \
      -k uvicorn.workers.UvicornWorker \
      --log-level debug
}

function start_env_k8s_prod() {
  source "${DS_SETUP_PATH}"
  activate_venv
  download_dependencies
  start_gunicorn gamechangerml.api.fastapi.mlapp:app \
      --bind 0.0.0.0:5000 \
      --workers 1 \
      --graceful-timeout 900 \
      --timeout 1200 \
      -k uvicorn.workers.UvicornWorker \
      --log-level debug
}

case "${ENV_TYPE}" in
  PROD)
    start_env_prod
    ;;
  DEV)
    start_env_dev
    ;;
  DEVLOCAL)
    start_env_devlocal
    ;;
  K8S_DEV)
    start_env_k8s_dev
    ;;
  K8S_TEST)
    start_env_k8s_test
    ;;
  K8S_PROD)
    start_env_k8s_prod
    ;;
  *)
    >&2 echo "[ERROR] Attempted to start with invalid ENV_TYPE specified: '$ENV_TYPE'"
    exit 1
    ;;
esac
