#!/usr/bin/env bash

set -o errexit
set -o nounset
set -o pipefail
set -o noclobber

readonly SCRIPT_PARENT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
readonly REPO_DIR="$( cd "$SCRIPT_PARENT_DIR/../../"  >/dev/null 2>&1 && pwd )"

# Load defaults
source "${SCRIPT_PARENT_DIR}/constants.conf"

# Set env vars
case "${DEPLOYMENT_ENV:-prod}" in
prod)
  SCANNER_UPLOADER_AWS_DEFAULT_REGION="us-gov-west-1"
  ;;
dev)
  SCANNER_UPLOADER_AWS_DEFAULT_REGION="us-east-1"
  ;;
*)
  echo >&2 "ERROR: Set valid DEPLOYMENT_ENV var (prod|dev)."
  exit 2
  ;;
esac

# Set job vars
case "${1:?ERROR: Missing job name arg}" in
gc_crawl_and_download)
  JOB_NAME="gc_crawl_and_download"
  CRAWLER_CONTAINER_IMAGE="$CORE_DOWNLOADER_IMAGE"
  SCANNER_UPLOADER_S3PATH="/gamechanger/external-uploads/crawler-downloader/$(date +%FT%T)"
  ;;
gc_crawl_and_download_covid)
  JOB_NAME="gc_crawl_and_download_covid"
  CRAWLER_CONTAINER_IMAGE="$COVID_DOWNLOADER_IMAGE"
  SCANNER_UPLOADER_S3PATH="/gamechanger/external-uploads/covid-crawler-downloader/$(date +%FT%T)"
  ;;
*)
  echo >&2 "ERROR: Pass valid job name to the script."
  exit 2
  ;;
esac

# base dir where container-mounted temporary subdirs are created
HOST_JOB_TMP_DIR="${HOST_JOB_TMP_DIR:-${2:?"ERROR: Set HOST_JOB_TMP_DIR or pass it as a second argument"}}"
if [ ! -d "$HOST_JOB_TMP_DIR" ]; then
  echo >&2 "ERROR: Given job tmp dir '$HOST_JOB_TMP_DIR' does not exist."
  exit 2
fi

# where files are downloaded before virus scan
HOST_JOB_DL_DIR="$HOST_JOB_TMP_DIR/$JOB_NAME/$(date +%Y%m%d_%H%M%S)"
# where files are downloaded from container's perspective
CRAWLER_CONTAINER_DL_DIR="/var/tmp/output"
# where files to be scanned are mounted inside scanner container
SCANNER_SCAN_DIR="$CRAWLER_CONTAINER_DL_DIR"
# general S3 bucket settings
SCANNER_UPLOADER_BUCKET="advana-raw-zone"
# path to the manifest to download in s3
SCANNER_UPLOADER_S3PATH_MANIFEST="/gamechanger/pdf/manifest.json"
# full path for S3 manifest
S3FULLPATH_MANIFEST="s3://${SCANNER_UPLOADER_BUCKET}/${SCANNER_UPLOADER_S3PATH_MANIFEST#/}"
# previous manifest location
LOCAL_PREVIOUS_MANIFEST_LOCATION="$REPO_DIR/paasJobs/docker/crawl_and_download/previous-manifest.json"


#####
## ## Main Procedures
#####

function purge_host_dl_dir() {
    if [ -d "$HOST_JOB_DL_DIR" ]; then
      rm -rf "$HOST_JOB_DL_DIR"
    fi
}

function recreate_host_dl_dir() {
    # purge and recreate host DL dir if it exists
    purge_host_dl_dir
    mkdir -p "$HOST_JOB_DL_DIR"
}

function grab_manifest() {
  echo -e "\nGRABBING LATEST MANIFEST\n"
  (aws s3 cp ${S3FULLPATH_MANIFEST} ${LOCAL_PREVIOUS_MANIFEST_LOCATION}) || echo -e "\nFAILED TO GRAB MANIFEST\n"
}

function run_crawler_downloader() {
  local container_name="$JOB_NAME"
  docker rm --force "$container_name" || true

  echo "Running crawler container: $container_name"
  docker run \
    --name "$container_name" \
    -u "$(id -u):$(id -g)" \
    -e "LOCAL_DOWNLOAD_DIRECTORY_PATH=${CRAWLER_CONTAINER_DL_DIR}" \
    -e "TEST_RUN=${TEST_RUN:-no}" \
    "${CRAWLER_CONTAINER_IMAGE}" \
  && docker cp "$container_name":"$CRAWLER_CONTAINER_DL_DIR" "$HOST_JOB_DL_DIR"
  local docker_run_status=$?

  docker rm "$container_name" || true
  return $docker_run_status
}

function run_scanner_uploader() {
  local inner_job_dl_dir="${HOST_JOB_DL_DIR}/$(basename "$CRAWLER_CONTAINER_DL_DIR")"

  printf "\n\n>>> RUNNING SCANNER CONTAINER <<<\n"
  printf "\tHost scan dir is %s \n" "$inner_job_dl_dir"
  printf "\tMounted in scanner container at %s \n\n" "$SCANNER_SCAN_DIR"

  docker run \
    --rm \
    -u "$(id -u):$(id -g)" \
    -v "${inner_job_dl_dir}:${SCANNER_SCAN_DIR}:z" \
    -e "AWS_DEFAULT_REGION=${SCANNER_UPLOADER_AWS_DEFAULT_REGION}" \
    -e "BUCKET=${SCANNER_UPLOADER_BUCKET}" \
    -e "S3_UPLOAD_BASE_PATH=${SCANNER_UPLOADER_S3PATH}" \
    -e "DELETE_AFTER_UPLOAD=no" \
    -e "SKIP_S3_UPLOAD=${SKIP_S3_UPLOAD:-no}" \
    --entrypoint="python3" \
    "${SCANNER_UPLOADER_CONTAINER_IMAGE}" \
      "/srv/dlp-scanner/parallel-dlp-scanner.py" \
        --input-path "${SCANNER_SCAN_DIR}" \
        --scanner-path "/srv/dlp-scanner/dlp-scanner.sh"
}

#####
## ## Cleanup Hooks
#####

function cleanup_hooks() {
  purge_host_dl_dir
}

# keep files around for tourbleshooting if it's a test run
if [[ "${TEST_RUN:-no}" != "yes" ]]; then
  trap cleanup_hooks EXIT
fi

#####
## ## Run it
#####

SECONDS=0
cat <<EOF
  STARTING JOB - $JOB_NAME
  $(date "+DATE: %Y-%m-%d TIME: %H:%M:%S")
EOF

# make sure we have a fresh dir to put files into
recreate_host_dl_dir
# grab the previous manifest from s3, download files, and scan files & upload to s3
grab_manifest && run_crawler_downloader && run_scanner_uploader

cat <<EOF
  FINISHED JOB - $JOB_NAME
  $(date "+DATE: %Y-%m-%d TIME: %H:%M:%S")
EOF

# how long?
duration=$SECONDS
echo -e "\n $(($duration / 60)) minutes and $(($duration % 60)) seconds elapsed."