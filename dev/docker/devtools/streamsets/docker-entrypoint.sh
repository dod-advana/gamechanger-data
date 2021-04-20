#!/usr/bin/env bash
set -o errexit
set -o nounset

if [ "${BITBUCKET_GIT_CREDENTIALS:-}" ]; then
  # e.g. https://<bitbucket-username>:<bitbucket-token>@bitbucket.di2e.net
  echo "$BITBUCKET_GIT_CREDENTIALS" > "$HOME/.git-credentials"
  chmod 600 "$HOME/.git-credentials"
fi

sudo chown -R sdc:sdc "$SDC_DATA" "$SDC_LOG"
"$SDC_HOME/bin/streamsets" dc -verbose