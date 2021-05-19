#!/usr/bin/env bash
set -o nounset
set -o errexit
set -o pipefail

#####
## ## JOB RUNNER
#####  - wrapper for running ad-hoc jobs, sending notifications, uploading logs
#
## USAGE:
##    job_runner.sh <location-of-the-job-conf-file>
#
## EXAMPLE: job.conf file - params affect how notifications/logs are handled and which job script is launched
#
# JOB_NAME="Dummy Job"
# JOB_SCRIPT="/gamechanger-data/tmp/dummy_job.sh"
# SEND_NOTIFICATIONS="yes"
# UPLOAD_LOGS="no"
# SLACK_HOOK_CHANNEL="#gc-alerts-dev"
# SLACK_HOOK_URL="https://hooks.slack.com/services/12312123/3534153245"
# S3_BASE_LOG_PATH_URL="s3://somebucket/someplace"
# AWS_DEFAULT_REGION="us-east-1"

function send_notification() {
  if [[ "${SEND_NOTIFICATIONS}" == "yes" ]] ; then
    >&2 echo "[INFO] Sending notifications ..."

    local text="$1"
    local json_data='{"channel":"'"$SLACK_HOOK_CHANNEL"'","text":"'"$text"'"}'

    curl --header "Content-Type: application/json" \
      --request POST \
      --data "$json_data" \
      "$SLACK_HOOK_URL"

    >&2 echo
    return "$?"
  else
    >&2 echo "[SKIPPING] Sending notifications ..."
    return 0
  fi
}

function upload_logs() {
  if [[ "${UPLOAD_LOGS}" == "yes" ]]; then
    >&2 echo "[INFO] Uploading logs ..."
    local local_log_path="$1"
    local s3_log_path="$2"

    ${AWS_CMD:-aws} s3 cp "$local_log_path" "$s3_log_path"
    return "$?"
  else
    >&2 echo "[SKIPPING] Uploading logs ..."
    return 0
  fi
}

function run_pre_checks() {
cat <<EOF
  Pre-checks for job: "$JOB_NAME"
    Job Conf:
      JOB_NAME: "${JOB_NAME}"
      JOB_SCRIPT: "${JOB_SCRIPT}"
      SEND_NOTIFICATIONS: "${SEND_NOTIFICATIONS}"
      UPLOAD_LOGS:   "${UPLOAD_LOGS}"
      SLACK_HOOK_CHANNEL: "${SLACK_HOOK_CHANNEL}"
      SLACK_HOOK_URL (is set?): $( [[ -z "${SLACK_HOOK_URL:-}" ]] && echo no || echo yes )
      S3_BASE_LOG_PATH_URL: "${S3_BASE_LOG_PATH_URL}"
      AWS_DEFAULT_REGION: "${AWS_DEFAULT_REGION:-us-east-1(default)}"
EOF

  if [[ -z "${SLACK_HOOK_URL:-}" ]]; then
    >&2 echo "[ERROR] SLACK_HOOK_URL is unset, check job config ..."
    exit 1
  fi
}

# runs in subshell, should not depend on anything in this wrapper
function run_job() (
  >&2 printf "Running job %s :: through :: %s\n" "$JOB_NAME" "$JOB_SCRIPT"
  bash "$JOB_SCRIPT"
  return "$?"
)

JOB_CONF="${1?Must provide job configuration file}"
source "$JOB_CONF"

TMP_LOG_FILE="$(mktemp)"
START_TS=$(date +"%Y-%m-%dT%H:%M:%S")
S3_LOG_FILE_PATH="$S3_BASE_LOG_PATH_URL/${JOB_NAME}.${START_TS}.log"

SECONDS=0

run_pre_checks && send_notification "[STARTED] JOB - ${JOB_NAME}\n\tLOG: \`$S3_LOG_FILE_PATH\`"

run_job 2>&1 | tee -a "$TMP_LOG_FILE" && rc=$? || rc=$?
if [[ $rc -eq 0 ]]; then
  NOTIFICATION_MSG="[SUCCESS] JOB - $JOB_NAME"
else
  NOTIFICATION_MSG="[FAILED] JOB - $JOB_NAME"
fi
send_notification "$NOTIFICATION_MSG \n\tLOG: \`$S3_LOG_FILE_PATH\`\n\tDuration: $(($SECONDS / 60)) minutes and $(($SECONDS % 60)) seconds"
upload_logs "$TMP_LOG_FILE" "$S3_LOG_FILE_PATH"  && rm -f "$TMP_LOG_FILE"