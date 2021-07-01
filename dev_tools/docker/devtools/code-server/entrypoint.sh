#!/bin/bash
set -o errexit
set -o nounset
# [MIT License] borrowed in part from https://github.com/cdr/code-server/tree/master/ci/release-image

# We do this first to ensure sudo works below when renaming the user.
# Otherwise the current container UID may not exist in the passwd database.
eval "$(fixuid -q)"

if [ "${DOCKER_USER-}" ]; then
  echo "$DOCKER_USER ALL=(ALL) NOPASSWD:ALL" | sudo tee -a /etc/sudoers.d/nopasswd > /dev/null
  # Unfortunately we cannot change $HOME as we cannot move any bind mounts
  # nor can we bind mount $HOME into a new home as that requires a privileged container.
  sudo usermod --login "$DOCKER_USER" "$CODE_SERVER_USER"
  sudo groupmod -n "$DOCKER_USER" "$CODE_SERVER_GROUP"

  USER="$DOCKER_USER"

  sudo sed -i "/coder/d" /etc/sudoers.d/nopasswd
fi

# for sudo-less docker CLI access on unix
# make sure user has same group membership as the mounted docker socket
# TODO: see if fixuid can be used here or if we can just rebase on portainer images
if  [[ "${DOCKER_HOST-}" == unix://* ]]; then

  DOCKER_SOCK=${DOCKER_HOST#unix://}
  DOCKER_GROUP_GID=$(getent group docker | cut -d: -f3)
  DOCKER_SOCK_GID=$(ls -n "$DOCKER_SOCK" | cut -d' ' -f4)
  DOCKER_SOCKET_GROUP=docker_socket_group

  # if docker sock is mounted with some other GID, make sure we have a corresponding group matching user
  if [ "${DOCKER_GROUP_GID}" -ne "${DOCKER_SOCK_GID}" ]; then

    if ( getent group | grep -q -P "\b${DOCKER_SOCK_GID}\b" ); then
      MATCHING_SOCK_GROUP=$(getent group | grep -P "\b${DOCKER_SOCK_GID}\b" | head -1 | cut -d: -f1)
      sudo usermod -aG $MATCHING_SOCK_GROUP $USER
    else
      sudo groupadd -g $DOCKER_SOCK_GID $DOCKER_SOCKET_GROUP
      sudo usermod -aG $DOCKER_SOCKET_GROUP $USER
    fi
  fi
fi

if [ "${BITBUCKET_GIT_CREDENTIALS:-}" ]; then
  # e.g. https://<bitbucket-username>:<bitbucket-token>@bitbucket.di2e.net
  echo "$BITBUCKET_GIT_CREDENTIALS" > "$HOME/.git-credentials"
  chmod 600 "$HOME/.git-credentials"
fi

tini -s -- /usr/bin/code-server $@