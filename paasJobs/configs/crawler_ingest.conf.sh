#!/usr/bin/env bash

#####
## ## CRAWLER INGEST JOB CONFIG
#####
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
readonly REPO_DIR="$( cd "$SCRIPT_PARENT_DIR/../../"  >/dev/null 2>&1 && pwd )"

## BASE JOB_CONF

JOB_NAME="${JOB_NAME:-Crawler_Ingest}"
JOB_SCRIPT="${REPO_DIR}/paasJobs/scripts/crawler_ingest/crawler_ingest.sh"
SEND_NOTIFICATIONS="${SEND_NOTIFICATIONS:-yes}"
UPLOAD_LOGS="${UPLOAD_LOGS:-yes}"
SLACK_HOOK_CHANNEL="${SLACK_HOOK_CHANNEL}"
SLACK_HOOK_URL="${SLACK_HOOK_URL}"
S3_BASE_LOG_PATH_URL="${S3_BASE_LOG_PATH_URL:-s3://advana-raw-zone/gamechanger/data-pipelines/orchestration/logs/core-crawler-ingest}"
AWS_DEFAULT_REGION="${AWS_DEFAULT_REGION:-us-gov-west-1}"

## JOB SPECIFIC CONF

export ES_INDEX_NAME="${ES_INDEX_NAME:-gamechanger_20210409}"
export ES_ALIAS_NAME="${ES_ALIAS_NAME:-}"

export MAX_OCR_THREADS_PER_FILE="${MAX_OCR_THREADS_PER_FILE:-2}"
export MAX_PARSER_THREADS="${MAX_PARSER_THREADS:-16}"
export MAX_NEO4J_THREADS="${MAX_NEO4J_THREADS:-16}"

export S3_BUCKET_NAME="${S3_BUCKET_NAME:-advana-raw-zone}"

export SKIP_NEO4J_UPDATE="${SKIP_NEO4J_UPDATE:-no}"
export SKIP_SNAPSHOT_BACKUP="${SKIP_SNAPSHOT_BACKUP:-yes}"
export SKIP_DB_BACKUP="${SKIP_DB_BACKUP:-no}"
export SKIP_DB_UPDATE="${SKIP_DB_UPDATE:-no}"
export SKIP_REVOCATION_UPDATE="${SKIP_REVOCATION_UPDATE-no}"

export JOB_NAME="${JOB_NAME-core-crawler-ingest}"
export RELATIVE_CRAWLER_OUTPUT_LOCATION="${RELATIVE_CRAWLER_OUTPUT_LOCATION-raw_docs/crawler_output.json}"

