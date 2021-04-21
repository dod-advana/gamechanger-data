#!/usr/bin/env bash

#####
## ## Sensible bash script defaults
#####

set -o errexit
set -o nounset
set -o pipefail
set -o noclobber

readonly SCRIPT_PARENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
readonly LOCAL_REPO_DIR="$(cd "${SCRIPT_PARENT_DIR}/../../" >/dev/null 2>&1 && pwd)"

#####
## ## Docker build settings
#####

# set build tag here
readonly BUILD_TAG="gamechanger_crawl_and_download_covid:latest"
# set args here
readonly RAW_BUILD_ARGS="FOO=foo;BAR=bar"

function get_build_opt_string() {
  OLD_IFS="$IFS"
  IFS=";"

  local _build_args=""
  for arg in $RAW_BUILD_ARGS; do
    _build_args="${_build_args} --build-arg=$arg"
  done

  IFS="$OLD_IFS"
  echo "$_build_args"
}

readonly DOCKER_BUILD_CONTEXT_PATH="${LOCAL_REPO_DIR}"
readonly DOCKERFILE_PATH="${LOCAL_REPO_DIR}/paasJobs/crawl_and_download_covid/Dockerfile"
readonly BUILD_ARG_OPTS=$(get_build_opt_string)

#####
## ## Build the image
#####

set -x
docker build \
  $BUILD_ARG_OPTS \
  --tag "$BUILD_TAG" \
  --file "$DOCKERFILE_PATH" \
  "${DOCKER_BUILD_CONTEXT_PATH}"
