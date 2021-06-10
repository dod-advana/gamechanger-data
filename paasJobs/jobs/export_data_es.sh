#!/usr/bin/env bash

set -o errexit
set -o nounset
set -o pipefail

#####
## ## MAIN COMMANDS
#####

function run_core_ingest() {

  local pdf_s3_prefix="$PDF_S3_PREFIX"
  local json_s3_prefix="$JSON_S3_PREFIX"
  local s3_upload_prefix="$S3_UPLOAD_PREFIX"
  local job_tmp_dir="$JOB_TMP_DIR"
  local manifest_filename="${MANIFEST_FILENAME:-checksum_manifest.json}"
  local chunk_size="${CHUNK_SIZE:-1G}"

  python dataPipelines/scripts/es_export.py \
    --pdf-s3-prefix "$pdf_s3_prefix" \
    --json-s3-prefix "$json_s3_prefix" \
    --s3-upload-prefix "$s3_upload_prefix" \
    --job-tmp-dir "$job_tmp_dir" \
    --manifest-filename "$manifest_filename" \
    --chunk-size "$chunk_size"

}

##### ##### #####
## ## ## ## ## ## ACTUAL EXEC FLOW
##### ##### #####

SECONDS=0
cat <<EOF

  STARTING PIPELINE RUN
  $(date "+DATE: %Y-%m-%d TIME: %H:%M:%S")

EOF

# main
run_core_ingest

cat <<EOF

  SUCCESSFULLY FINISHED PIPELINE RUN
  $(date "+DATE: %Y-%m-%d TIME: %H:%M:%S")

EOF

# how long?
duration=$SECONDS
echo -e "\n $(( $SECONDS / 3600 ))h $(( ($SECONDS % 3600)/60 ))m $(($SECONDS % 60))s elapsed."
