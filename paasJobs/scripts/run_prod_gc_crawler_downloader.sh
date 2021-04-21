#!/usr/bin/env bash

set -o errexit
set -o nounset
set -o pipefail

readonly SCRIPT_PARENT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
readonly REPO_DIR="$( cd "$SCRIPT_PARENT_DIR/../../"  >/dev/null 2>&1 && pwd )"

# Load defaults
source "${SCRIPT_PARENT_DIR}/constants.conf"


# change it on deploy time if it doesn't work
export DEPLOYMENT_ENV="${DEPLOYMENT_ENV:-prod}"
export HOST_JOB_TMP_DIR="/gamechanger/jobs/"
export JOB_LOG_FILE="/gamechanger/jobs/logs/gc-crawler-downloader.$(date --iso-8601=seconds).log"

# change to "yes" in order to only crawl/download couple pubs for test purposes
export TEST_RUN="${TEST_RUN:-no}"

cat <<EOF
About to run the GC CRAWLER/DOWNLOADER JOB ...
  DEPLOYMENT_ENV is "$DEPLOYMENT_ENV"
  HOST_JOB_TMP_DIR is "$HOST_JOB_TMP_DIR"
  JOB_LOG_FILE is "$JOB_LOG_FILE"

EOF

echo "SENDING NOTIFICATIONS TO: ${NOTIFICATION_EMAIL}"
export NOTIFICATION_EMAIL

source "${SCRIPT_PARENT_DIR}/../../dataPipelines/scripts/email_notifications_utils.sh"

# email start
send_email_notification "CRAWLER DOWNLOADER" "STARTING"

touch "$JOB_LOG_FILE"
"$SCRIPT_PARENT_DIR/gc_crawl_then_upload.sh" gc_crawl_and_download 2>&1 | tee "$JOB_LOG_FILE"

# email end
send_email_notification "CRAWLER DOWNLOADER" "FINISHED"
