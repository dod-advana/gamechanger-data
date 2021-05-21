#!/usr/bin/env bash

set -o errexit
set -o nounset
set -o pipefail
set -o noclobber

readonly SCRIPT_PARENT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
readonly SETTINGS_CONF_PATH="$SCRIPT_PARENT_DIR/settings.conf"

#####
## ## LOAD SETTINGS
#####

source "$SETTINGS_CONF_PATH"

#####
## ## SETUP FUNCTIONS
#####

function setup_local_vars_and_dirs() {

  LOCAL_CRAWLER_OUTPUT_FILE_PATH="$LOCAL_DOWNLOAD_DIRECTORY_PATH/crawler_output.json"
  LOCAL_JOB_LOG_PATH="$LOCAL_DOWNLOAD_DIRECTORY_PATH/job.log"
  LOCAL_PREVIOUS_MANIFEST_LOCATION="$SCRIPT_PARENT_DIR/previous-manifest.json"
  LOCAL_NEW_MANIFEST_PATH="$LOCAL_DOWNLOAD_DIRECTORY_PATH/manifest.json"

  if [[ ! -d "$LOCAL_DOWNLOAD_DIRECTORY_PATH" ]]; then
    mkdir -p "$LOCAL_DOWNLOAD_DIRECTORY_PATH"
  fi

  touch "$LOCAL_JOB_LOG_PATH"

  echo LOCAL_DOWNLOAD_DIRECTORY_PATH is "$LOCAL_DOWNLOAD_DIRECTORY_PATH"

}

#####
## ## MAIN FUNCTIONS
#####

function run_crawler() {

  if [[ "${TEST_RUN:-no}" == "yes" ]]; then
    echo -e "\n[TEST RUN] RUNNING US CODE CRAWLER\n"
    ( "$PYTHON_CMD" -m dataPipelines.gc_crawler.us_code run | head -2 | tee -a "$LOCAL_CRAWLER_OUTPUT_FILE_PATH" ) \
    || echo "^^^ CRAWLER ERROR ^^^"
    return 0
  fi

  set +o pipefail

  echo -e "\nRUNNING Chief National Guard Bureau CRAWLER - SCRAPY\n"
  ( scrapy runspider dataPipelines/gc_scrapy/gc_scrapy/spiders/chief_national_guard_bureau_spider.py -o $LOCAL_CRAWLER_OUTPUT_FILE_PATH ) \
    || echo "^^^ CRAWLER ERROR ^^^"

  echo -e "\nRUNNING Coast Guard CRAWLER - SCRAPY\n"
  ( scrapy runspider dataPipelines/gc_scrapy/gc_scrapy/spiders/coast_guard_spider.py -o $LOCAL_CRAWLER_OUTPUT_FILE_PATH ) \
    || echo "^^^ CRAWLER ERROR ^^^"

  echo -e "\nRUNNING AIR FORCE LIBRARY CRAWLER\n"
  ( "$PYTHON_CMD" -m dataPipelines.gc_crawler.air_force_pubs run | tee -a "$LOCAL_CRAWLER_OUTPUT_FILE_PATH" ) \
    || echo "^^^ CRAWLER ERROR ^^^"

  echo -e "\nRUNNING ARMY CRAWLER\n"
  ( "$PYTHON_CMD" -m dataPipelines.gc_crawler.army_pubs run | tee -a "$LOCAL_CRAWLER_OUTPUT_FILE_PATH" ) \
    || echo "^^^ CRAWLER ERROR ^^^"

  echo -e "\nRUNNING ARMY RESERVES CRAWLER\n"
  ( "$PYTHON_CMD" -m dataPipelines.gc_crawler.army_reserves run | tee -a "$LOCAL_CRAWLER_OUTPUT_FILE_PATH" ) \
    || echo "^^^ CRAWLER ERROR ^^^"

#  echo -e "\nRUNNING NAVY BUPERS CRAWLER\n"
#  ( "$PYTHON_CMD" -m dataPipelines.gc_crawler.bupers_pubs run | tee -a "$LOCAL_CRAWLER_OUTPUT_FILE_PATH" ) \
#    || echo "^^^ CRAWLER ERROR ^^^"

  echo -e "\nRUNNING DHA CRAWLER\n"
  ( "$PYTHON_CMD" -m dataPipelines.gc_crawler.dha_pubs run | tee -a "$LOCAL_CRAWLER_OUTPUT_FILE_PATH" ) \
    || echo "^^^ CRAWLER ERROR ^^^"

  echo -e "\nRUNNING DoD ISSUANCES CRAWLER\n"
  ( "$PYTHON_CMD" -m dataPipelines.gc_crawler.dod_issuances run | tee -a "$LOCAL_CRAWLER_OUTPUT_FILE_PATH" ) \
    || echo "^^^ CRAWLER ERROR ^^^"

  echo -e "\nRUNNING EXECUTIVE ORDER CRAWLER\n"
  ( "$PYTHON_CMD" -m dataPipelines.gc_crawler.ex_orders run | tee -a "$LOCAL_CRAWLER_OUTPUT_FILE_PATH" ) \
    || echo "^^^ CRAWLER ERROR ^^^"

  echo -e "\nRUNNING FMR CRAWLER\n"
  ( "$PYTHON_CMD" -m dataPipelines.gc_crawler.fmr_pubs run | tee -a "$LOCAL_CRAWLER_OUTPUT_FILE_PATH" ) \
    || echo "^^^ CRAWLER ERROR ^^^"

  echo -e "\nRUNNING INTELLIGENCE COMMUNITY CRAWLER\n"
  ( "$PYTHON_CMD" -m dataPipelines.gc_crawler.ic_policies run | tee -a "$LOCAL_CRAWLER_OUTPUT_FILE_PATH" ) \
    || echo "^^^ CRAWLER ERROR ^^^"

  echo -e "\nRUNNING JCS PUBLICATION CRAWLER\n"
  ( "$PYTHON_CMD" -m dataPipelines.gc_crawler.jcs_pubs run | tee -a "$LOCAL_CRAWLER_OUTPUT_FILE_PATH" ) \
    || echo "^^^ CRAWLER ERROR ^^^"

#  echo -e "\nRUNNING MARINE PUBLICATION CRAWLER\n"
#  ( "$PYTHON_CMD" -m dataPipelines.gc_crawler.marine_pubs run | tee -a "$LOCAL_CRAWLER_OUTPUT_FILE_PATH" ) \
#    || echo "^^^ CRAWLER ERROR ^^^"

#  echo -e "\nRUNNING MILPERSMAN CRAWLER\n"
#  ( "$PYTHON_CMD" -m dataPipelines.gc_crawler.milpersman_crawler run | tee -a "$LOCAL_CRAWLER_OUTPUT_FILE_PATH" ) \
#    || echo "^^^ CRAWLER ERROR ^^^"

  echo -e "\nRUNNING NATO STANAG CRAWLER\n"
  ( "$PYTHON_CMD" -m dataPipelines.gc_crawler.nato_stanag run | tee -a "$LOCAL_CRAWLER_OUTPUT_FILE_PATH" ) \
    || echo "^^^ CRAWLER ERROR ^^^"

  echo -e "\nRUNNING NAVY MED PUBS CRAWLER\n"
  ( "$PYTHON_CMD" -m dataPipelines.gc_crawler.navy_med_pubs run | tee -a "$LOCAL_CRAWLER_OUTPUT_FILE_PATH" ) \
    || echo "^^^ CRAWLER ERROR ^^^"

  echo -e "\nRUNNING NAVY RESERVES CRAWLER\n"
  ( "$PYTHON_CMD" -m dataPipelines.gc_crawler.navy_reserves run | tee -a "$LOCAL_CRAWLER_OUTPUT_FILE_PATH" ) \
    || echo "^^^ CRAWLER ERROR ^^^"

  echo -e "\nRUNNING OPM CRAWLER\n"
  ( "$PYTHON_CMD" -m dataPipelines.gc_crawler.opm_pubs run | tee -a "$LOCAL_CRAWLER_OUTPUT_FILE_PATH" ) \
    || echo "^^^ CRAWLER ERROR ^^^"

  echo -e "\nRUNNING SECNAV/OPNAV CRAWLER\n"
  ( "$PYTHON_CMD" -m dataPipelines.gc_crawler.secnav_pubs run | tee -a "$LOCAL_CRAWLER_OUTPUT_FILE_PATH" ) \
    || echo "^^^ CRAWLER ERROR ^^^"

  echo -e "\nRUNNING US CODE CRAWLER\n"
  ( "$PYTHON_CMD" -m dataPipelines.gc_crawler.us_code run | tee -a "$LOCAL_CRAWLER_OUTPUT_FILE_PATH" ) \
    || echo "^^^ CRAWLER ERROR ^^^"

   echo -e "\nRUNNING LEGISLATION CRAWLER\n"
  ( "$PYTHON_CMD" -m dataPipelines.gc_crawler.legislation_pubs run | tee -a "$LOCAL_CRAWLER_OUTPUT_FILE_PATH" ) \
    || echo "^^^ CRAWLER ERROR ^^^"

    echo -e "\nRUNNING DFAR/FAR CRAWLER\n"
  ( "$PYTHON_CMD" -m dataPipelines.gc_crawler.jumbo_dfar_far run | tee -a "$LOCAL_CRAWLER_OUTPUT_FILE_PATH" ) \
    || echo "^^^ CRAWLER ERROR ^^^"

#    echo -e "\nRUNNING FAR HTML CRAWLER\n"
#  ( "$PYTHON_CMD" -m dataPipelines.gc_crawler.far_subpart_regs run | tee -a "$LOCAL_CRAWLER_OUTPUT_FILE_PATH" ) \
#    || echo "^^^ CRAWLER ERROR ^^^"

#    echo -e "\nRUNNING DFAR HTML CRAWLER\n"
#  ( "$PYTHON_CMD" -m dataPipelines.gc_crawler.dfar_subpart_regs run | tee -a "$LOCAL_CRAWLER_OUTPUT_FILE_PATH" ) \
#    || echo "^^^ CRAWLER ERROR ^^^"

  set -o pipefail
}

function run_downloader() {
  echo -e "\nRUNNING DOWNLOADER\n"

  if [[ "${TEST_RUN:-no}" == "yes" ]]; then

    "$PYTHON_CMD" -m dataPipelines.gc_downloader download \
      --input-json "$LOCAL_CRAWLER_OUTPUT_FILE_PATH" \
      --output-dir "$LOCAL_DOWNLOAD_DIRECTORY_PATH" \
      --new-manifest "$LOCAL_NEW_MANIFEST_PATH"

  else

    "$PYTHON_CMD" -m dataPipelines.gc_downloader download \
      --input-json "$LOCAL_CRAWLER_OUTPUT_FILE_PATH" \
      --output-dir "$LOCAL_DOWNLOAD_DIRECTORY_PATH" \
      --new-manifest "$LOCAL_NEW_MANIFEST_PATH" \
      --previous-manifest "$LOCAL_PREVIOUS_MANIFEST_LOCATION"
  fi

  echo -e "\nDOWNLOADED FILES LOCATED AT: $LOCAL_DOWNLOAD_DIRECTORY_PATH \n"
}

function register_log_in_manifest() {
  "$PYTHON_CMD" -m dataPipelines.gc_downloader add-to-manifest --file "$LOCAL_JOB_LOG_PATH" --manifest "$LOCAL_NEW_MANIFEST_PATH"
}

function register_crawl_log_in_manifest() {
  "$PYTHON_CMD" -m dataPipelines.gc_downloader add-to-manifest --file "$LOCAL_CRAWLER_OUTPUT_FILE_PATH" --manifest "$LOCAL_NEW_MANIFEST_PATH"
}

##### ##### #####
## ## ## ## ## ## ACTUAL EXEC FLOW
##### ##### #####

# setup
setup_local_vars_and_dirs

SECONDS=0
cat <<EOF 2>&1 | tee -a "$LOCAL_JOB_LOG_PATH"

  STARTING PIPELINE RUN
  $(date "+DATE: %Y-%m-%d TIME: %H:%M:%S")

EOF

# run
run_crawler 2>&1 | tee -a "$LOCAL_JOB_LOG_PATH"
run_downloader 2>&1 | tee -a "$LOCAL_JOB_LOG_PATH"

cat <<EOF 2>&1 | tee -a "$LOCAL_JOB_LOG_PATH"

  SUCCESSFULLY FINISHED PIPELINE RUN
  $(date "+DATE: %Y-%m-%d TIME: %H:%M:%S")

EOF

# how long?
duration=$SECONDS
echo -e "\n $(($duration / 60)) minutes and $(($duration % 60)) seconds elapsed." 2>&1 | tee -a "$LOCAL_JOB_LOG_PATH"

# register additional files in manifest
register_log_in_manifest
register_crawl_log_in_manifest
