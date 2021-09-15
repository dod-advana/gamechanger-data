#!/usr/bin/env bash

readonly SCRIPT_PARENT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
readonly REPO_DIR="$( cd "$SCRIPT_PARENT_DIR/../../../"  >/dev/null 2>&1 && pwd )"

## BASE JOB_CONF

JOB_NAME="MONITORING: CREATE CLONE"
JOB_SCRIPT="${REPO_DIR}/paasJobs/jobs/create_clone.sh"
SLACK_HOOK_CHANNEL="${SLACK_HOOK_CHANNEL}"
SLACK_HOOK_URL="${SLACK_HOOK_URL}"
AWS_DEFAULT_REGION="${AWS_DEFAULT_REGION:-us-gov-west-1}"
VENV_ACTIVATE_SCRIPT="${VENV_ACTIVATE_SCRIPT:-/opt/gc-venv-current/bin/activate}"

SEND_NOTIFICATIONS="${SEND_NOTIFICATIONS:-no}"
UPLOAD_LOGS="${UPLOAD_LOGS:-yes}"
S3_BASE_LOG_PATH_URL="${S3_BASE_LOG_PATH_URL:-s3://advana-data-zone/bronze/gamechanger/data-pipelines/orchestration/logs/core-s3-ingest}"
CLEANUP="${CLEANUP:-yes}"
TMPDIR="${TMPDIR:-/data/tmp}"
