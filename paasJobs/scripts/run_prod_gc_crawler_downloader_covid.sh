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
export HOST_JOB_TMP_DIR="/mnt/s3-unpack-n-scan/gamechanger"
export JOB_LOG_FILE="/mnt/s3-unpack-n-scan/gamechanger/logs/gc-covid-crawler-downloader.log"

cat <<EOF
About to run the GC COVID CRAWLER/DOWNLOADER JOB ...
  DEPLOYMENT_ENV is "$DEPLOYMENT_ENV"
  HOST_JOB_TMP_DIR is "$HOST_JOB_TMP_DIR"
  JOB_LOG_FILE is "$JOB_LOG_FILE"

EOF

touch "$JOB_LOG_FILE"
"$SCRIPT_PARENT_DIR/gc_crawl_then_upload.sh" gc_crawl_and_download_covid 2>&1 | tee "$JOB_LOG_FILE"