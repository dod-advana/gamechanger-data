# THESE ARE BASH UTILS, MEANT TO BE SOURCED - e.g. `source ./dev_ecr_utils.sh` - for subsequent use
export AWS_ACCESS_KEY_ID="SET ME"
export AWS_SECRET_ACCESS_KEY="SET ME"
export AWS_SESSION_TOKEN="SET ME"

ECR_REGISTRY="SET ME"

function ecr_docker_login() {
  aws ecr get-login-password --region "us-east-1" | docker login --username AWS --password-stdin "$ECR_REGISTRY"
}

function get_ecr_tag() {
  # bare tag doesn't have the ECR registry url in front of it, e.g. image:latest instead of ecr.address/image:latest
  local bare_image_tag="$1"

  printf "%s/%s" "$ECR_REGISTRY" "$bare_image_tag"
}

function tag_image_for_ecr() {
  # bare tag doesn't have the ECR registry url in front of it, e.g. image:latest instead of ecr.address/image:latest
  local bare_image_tag="$1"
  local ecr_tag=$(get_ecr_tag "$bare_image_tag")

  docker tag "$bare_image_tag" "$ecr_tag"
}

function tag_and_push_to_ecr() {
  # bare tag doesn't have the ECR registry url in front of it, e.g. image:latest instead of ecr.address/image:latest
  local bare_image_tag="$1"
  local ecr_tag=$(get_ecr_tag "$bare_image_tag")

  tag_image_for_ecr "$bare_image_tag"
  docker push "$ecr_tag"
}

function pull_image_from_ecr() {
  # bare tag doesn't have the ECR registry url in front of it, e.g. image:latest instead of ecr.address/image:latest
  local bare_image_tag="${1:-$1}"
  local ecr_tag=$(get_ecr_tag "$bare_image_tag")

  docker pull "$ecr_tag"
  docker tag "$ecr_tag" "$bare_image_tag"
}
