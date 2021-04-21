#!/usr/bin/env bash

set -o errexit
set -o nounset
set -o pipefail
set -o noclobber

readonly SCRIPT_PARENT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
readonly REPO_DIR="$( cd "$SCRIPT_PARENT_DIR/../../"  >/dev/null 2>&1 && pwd )"

# Load defaults
source "${SCRIPT_PARENT_DIR}/constants.conf"

DEPLOYMENT_ENV=${DEPLOYMENT_ENV:-prod}

echo "Rebuilding $SCANNER_UPLOADER_CONTAINER_IMAGE image"
docker build -f "$REPO_DIR/paasJobs/docker/scanner_uploader/${DEPLOYMENT_ENV}.Dockerfile" \
  -t "$SCANNER_UPLOADER_CONTAINER_IMAGE" \
  "$REPO_DIR/paasJobs/docker/scanner_uploader/"