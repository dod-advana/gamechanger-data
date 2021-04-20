#!/usr/bin/env bash

set -o errexit
set -o nounset
set -o pipefail

readonly SCRIPT_PARENT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
readonly REPO_DIR="$( cd "$SCRIPT_PARENT_DIR/../../"  >/dev/null 2>&1 && pwd )"

# Load defaults
source "${SCRIPT_PARENT_DIR}/constants.conf"

export SKIP_BASE_IMAGES="no"
export DEPLOYMENT_ENV="${DEPLOYMENT_ENV:-prod}"

"$SCRIPT_PARENT_DIR/rebuild_images.sh"