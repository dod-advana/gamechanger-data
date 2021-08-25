#!/usr/bin/env bash

#####
## ## TEST JOB CONFIG
##### -- for checking behavior of the job runner
#
## USAGE (CRON or OTHERWISE):
#     env <envvar1=val1 envvar2=val2 ...> <path-to/job_runner.sh> <path-to/this.conf.sh>
#
## NOTE all env vars that don't have defaults must be exported ahead of time or passed via `env` command
#
## MINIMAL EXAMPLE:
#     env SLACK_HOOK_CHANNEL="#some-channel" SLACK_HOOK_URL="https://slack/hook" /app/job_runner.sh /app/somejob.conf.sh
#

readonly SCRIPT_PARENT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
readonly REPO_DIR="$( cd "$SCRIPT_PARENT_DIR/../../../"  >/dev/null 2>&1 && pwd )"

## BASE JOB_CONF

JOB_NAME="${JOB_NAME:-Test}"
JOB_SCRIPT="${REPO_DIR}/paasJobs/jobs/test_job.sh"
SEND_NOTIFICATIONS="${SEND_NOTIFICATIONS:-yes}"
UPLOAD_LOGS="${UPLOAD_LOGS:-yes}"
SLACK_HOOK_CHANNEL="${SLACK_HOOK_CHANNEL}"
SLACK_HOOK_URL="${SLACK_HOOK_URL}"
S3_BASE_LOG_PATH_URL="${S3_BASE_LOG_PATH_URL:-s3://advana-data-zone/bronze/gamechanger/data-pipelines/orchestration/logs/test-job}"
AWS_DEFAULT_REGION="${AWS_DEFAULT_REGION:-us-gov-west-1}"
TMPDIR="${TMPDIR:-/data/tmp}"
VENV_ACTIVATE_SCRIPT="${VENV_ACTIVATE_SCRIPT:-/opt/gc-venv-current/bin/activate}"
# PYTHONPATH="${PYTHONPATH:-$REPO_DIR}
