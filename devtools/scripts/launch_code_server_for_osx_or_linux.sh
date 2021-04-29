#!/usr/bin/env bash

#####
## ## GC CODE SERVER - Visual Studio Code env with all GC packages and dependencies
#####

#
###
#### Use env vars to override launch defaults
###
#

# name of the container
CODE_SERVER_CONTAINER_NAME="${CODE_SERVER_CONTAINER_NAME:-code-server}"
# password to the web ui
CODE_SERVER_PASSWORD="${CODE_SERVER_PASSWORD:-password}"
# credentials used to authenticate to bitbucket (or any other git repo, really)
## format: https://<bitbucket-username>:<bitbucket-token>@bitbucket.di2e.net
CODE_SERVER_BITBUCKET_GIT_CREDENTIALS="${CODE_SERVER_BITBUCKET_GIT_CREDENTIALS:-}"
# flag on whether to remove old container before starting: (yes|no)
CODE_SERVER_RECREATE_CONTAINER="${CODE_SERVER_RECREATE_CONTAINER:-yes}"
# port where the code server UI will bind on docker host
CODE_SERVER_BIND_PORT="${CODE_SERVER_BIND_PORT:-8080}"
# IP where the code server UI will bind on docker host, set 0.0.0.0 to bind on all ports (for remote access)
CODE_SERVER_BIND_IP="${CODE_SERVER_BIND_IP:-127.0.0.1}"
# host directory where code-server configuration will be stored, it is mounted into the docker container
CODE_SERVER_CONFIG_BIND_DIR="${CODE_SERVER_CONFIG_BIND_DIR:-"$HOME/.config"}"
# workspace directory from host that gets mounted into the docker container, e.g. a repo directory
CODE_SERVER_WORKSPACE_BIND_DIR="${CODE_SERVER_WORKSPACE_BIND_DIR:-"$PWD"}"
# user id that will be assumed by code-server user
CODE_SERVER_USER_ID="${CODE_SERVER_USER_ID:-$(id -u)}"
# group id that will be assumed by the code-server user
CODE_SERVER_GROUP_ID="${CODE_SERVER_GROUP_ID:-$(id -g)}"
# username that will be assumed by the code-server user
CODE_SERVER_USERNAME="${CODE_SERVER_USERNAME:-$USER}"
# image used to launch the code server container
CODE_SERVER_IMAGE_NAME="${CODE_SERVER_IMAGE_NAME:-"gc_code_server:latest"}"

mkdir -p ~/.config

if [[ "${CODE_SERVER_RECREATE_CONTAINER}" == "yes" ]]; then
  docker rm --force "$CODE_SERVER_CONTAINER_NAME" || true
fi

docker run -d --name "$CODE_SERVER_CONTAINER_NAME" -p "${CODE_SERVER_BIND_IP}:${CODE_SERVER_BIND_PORT}:8080" \
  -v "${CODE_SERVER_CONFIG_BIND_DIR}:/home/coder/.config" \
  -v "${CODE_SERVER_WORKSPACE_BIND_DIR}:/home/coder/project" \
  -u "${CODE_SERVER_USER_ID}:${CODE_SERVER_GROUP_ID}" \
  -e "DOCKER_USER=$CODE_SERVER_USERNAME" \
  -e "PASSWORD=$CODE_SERVER_PASSWORD" \
  -e "BITBUCKET_GIT_CREDENTIALS=$CODE_SERVER_BITBUCKET_GIT_CREDENTIALS" \
  "$CODE_SERVER_IMAGE_NAME"

cat <<EOF

Code server container is running.

If running locally, connect in the browser at:
  https://localhost:$CODE_SERVER_BIND_PORT

To follow logs, run:
  docker logs -f "$CODE_SERVER_CONTAINER_NAME"

EOF
echo "Code server container is running. logs with 'docker logs -f '"