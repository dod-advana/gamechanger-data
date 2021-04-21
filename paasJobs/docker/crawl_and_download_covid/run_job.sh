#!/usr/bin/env bash

set -o errexit
set -o nounset
set -o pipefail
set -o noclobber

readonly SCRIPT_PARENT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
readonly SETTINGS_CONF_PATH="$SCRIPT_PARENT_DIR/settings.conf"
readonly SANITY_CHECKS_CONF_PATH="$SCRIPT_PARENT_DIR/sanity_checks.conf"

export TMPDIR="${BASE_LOCAL_TMP_DIR:-$TMPDIR}"

#####
## ## LOAD SETTINGS
#####

source "$SETTINGS_CONF_PATH"
source "$SANITY_CHECKS_CONF_PATH"

#####
## ## SETUP TMP DIR
#####

function setup_tmp_dir() {
  LOCAL_TMP_DIR=$(mktemp -d)
}
setup_tmp_dir # CALLING RIGHT AWAY (to avoid issues with unbound var later)

function echo_tmp_dir_locaton() {
  echo -e "\nTEMP DIR IS AT $LOCAL_TMP_DIR \n"
}

function remove_tmp_dir() {
  if [[ -d "$LOCAL_TMP_DIR" ]]; then
    rm -r "$LOCAL_TMP_DIR"
  fi
}

#####
## ## REGISTER CLEANUP HOOKS
#####

function cleanup_hooks() {
  remove_tmp_dir
  # echo_tmp_dir_locaton
}
trap cleanup_hooks EXIT

#####
## ## SETUP FUNCTIONS
#####

function setup_local_vars_and_dirs() {

  LOCAL_JOB_LOG_PATH="$LOCAL_DOWNLOAD_DIRECTORY_PATH/job.log"

  mkdir -p "$LOCAL_DOWNLOAD_DIRECTORY_PATH"
  touch "$LOCAL_JOB_LOG_PATH"
}

#####
## ## MAIN FUNCTIONS
#####


function run_downloader() {
  echo -e "\nRUNNING DOWNLOADER\n"
  ( "$PYTHON_CMD" -m  dataPipelines.gc_covid_downloader run  --staging-folder "$LOCAL_DOWNLOAD_DIRECTORY_PATH" ) \
    || echo "^^^ CRAWLER ERROR ^^^"
}

function register_log_in_manifest() {
  "$PYTHON_CMD" -m dataPipelines.gc_downloader add-to-manifest --file "$LOCAL_JOB_LOG_PATH" --manifest "$LOCAL_NEW_MANIFEST_PATH"
}

function echo_downloaded_files_location() {
  echo -e "\nDOWNLOADED FILES LOCATED AT: $LOCAL_DOWNLOAD_DIRECTORY_PATH \n"
}

#####
## ## VALIDATION FUNCTIONS
#####

function check_number_of_downloaded_files() {
  local _files_downloaded=$(ls -1 "$LOCAL_DOWNLOAD_DIRECTORY_PATH" | wc -l)
  local _min_number_of_files="$EXPECTED_NUMBER_OF_FILES"

  if [[ "$_files_downloaded" -lt "$_min_number_of_files" ]]; then
    echo "CHECK - FAILED - Number of files downloaded - $_files_downloaded - is less than set minimum of $_min_number_of_files" && exit 123
  else
    echo "CHECK - OK - Downloaded at least $_min_number_of_files files. Total: $_files_downloaded"
  fi
}


##### ##### #####
## ## ## ## ## ## ACTUAL EXEC FLOW
##### ##### #####

# setup
echo_tmp_dir_locaton
setup_local_vars_and_dirs

SECONDS=0
cat <<EOF 2>&1 | tee -a "$LOCAL_JOB_LOG_PATH"

  STARTING PIPELINE RUN
  $(date "+DATE: %Y-%m-%d TIME: %H:%M:%S")

EOF

# run
run_downloader 2>&1 | tee -a "$LOCAL_JOB_LOG_PATH"
echo_downloaded_files_location 2>&1 | tee -a "$LOCAL_JOB_LOG_PATH"
# validate
check_number_of_downloaded_files 2>&1 | tee -a "$LOCAL_JOB_LOG_PATH"

cat <<EOF 2>&1 | tee -a "$LOCAL_JOB_LOG_PATH"

  SUCCESSFULLY FINISHED PIPELINE RUN
  $(date "+DATE: %Y-%m-%d TIME: %H:%M:%S")

EOF

# how long?
duration=$SECONDS
echo -e "\n $(($duration / 60)) minutes and $(($duration % 60)) seconds elapsed." 2>&1 | tee -a "$LOCAL_JOB_LOG_PATH"

# register log file in the manifest
register_log_in_manifest
