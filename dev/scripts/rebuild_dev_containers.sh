#!/usr/bin/env bash

set -o errexit
set -o nounset
set -o pipefail
set -o noclobber

readonly SCRIPT_PARENT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
readonly REPO_DIR="$( cd "$SCRIPT_PARENT_DIR/../../"  >/dev/null 2>&1 && pwd )"
readonly DEV_DOCKER_DIR="${REPO_DIR}/dev/docker"

readonly ECR_UTILS="$SCRIPT_PARENT_DIR/dev_ecr_utils.sh"
readonly REMOTE_DEV_DOCKER_REPO="${REMOTE_DEV_DOCKER_REPO:-10.194.9.80:5000}"

source "$ECR_UTILS"

function build_and_push() {
  local image_name="${1:?"Pass image name (must correspond to dir)"}"
  local dockerfile_path="${DEV_DOCKER_DIR}/${image_name#gamechanger/}/Dockerfile"

  if [[ ! -f "$dockerfile_path" ]]; then
    echo >&2 "There's no dockerfile for given image: $image_name at $dockerfile_path"
    exit 1
  fi

  local local_image_tag="${image_name}:latest"
  local remote_image_tag="${REMOTE_DEV_DOCKER_REPO}/${image_name}:latest"

  if [[ "${SKIP_BUILD:-yes}" != "no" ]]; then
      echo "Building image: $local_image_tag ..."
      docker build \
        --quiet \
        -f "$dockerfile_path" \
        -t "$local_image_tag" \
        -t "$remote_image_tag" \
        "${REPO_DIR}"

      docker system prune -f &> /dev/null
  fi

  if [[ "${SKIP_PUSH:-yes}" != "no" ]]; then
    echo "Pushing image: $remote_image_tag ..."
    docker push "$remote_image_tag"
  fi

}

for image in \
  gamechanger/data/models \
  gamechanger/core/{base,dev,ci}-env \
  gamechanger/devtools/streamsets \
  gamechanger/core/ml-api \
  gamechanger/core/crawler ; do

  build_and_push "$image"

  if [[ "${ECR_PUSH:-no}" == "yes" ]]; then
    echo "Pushing to ECR ..."
    tag_and_push_to_ecr "$image"
  fi

done
