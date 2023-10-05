#!/usr/bin/env bash


###################################################################################################
# SCRIPT DESCRIPTION:
# This script automates the process of deleting data related to a specific crawler in Gamechanger's
# system. It performs the following steps in sequence:
#
# 1. Downloads metadata files associated with all the crawlers from the specified S3 bucket.
# 2. Filters out the metadata files related to the desired crawler (specified by CRAWLER_NAME).
# 3. Deletes the relevant data across multiple destinations: S3, Postgres, Neo4j, and Elasticsearch.
# 4. Deletes the relevant records from S3 cumulative manifest.
# 5. Uploads the updated JSON metadata to a S3.
#
# USAGE:
# 1. Execute the script:
#    ./automated_delete_process.sh
#
# INPUTS:
# - CRAWLER_NAME: Specifies the name of the crawler whose data is to be deleted.
# - LOCAL_DIR: The local directory where metadata files will be temporarily stored.
# - OUTPUT_JSON: The name of the JSON file that will store filtered metadata.
# - S3_DESTINATION_PATH: The S3 path where the updated JSON will be uploaded.
#
# OUTPUT:
# - A display of the sequence of operations and their status.
# - Elapsed time of the entire process.
###################################################################################################


# Specify the crawler name
CRAWLER_NAME="CNSS" # Targeted crawler to delete

TIMESTAMP=$(date "+%Y-%m-%dT%H:%M:%S")  # This will generate a timestamp like 2023-10-05T16:08:01

mkdir -p ../../tmp/test/${CRAWLER_NAME}/${TIMESTAMP} # Create directory if not present
LOCAL_DIR="../../tmp/test/${CRAWLER_NAME}/${TIMESTAMP}"  # Specify the local directory path

LOG_FILE="${LOCAL_DIR}/${CRAWLER_NAME}_automated_delete_process.log"
ERROR_LOG_FILE="${LOCAL_DIR}/${CRAWLER_NAME}_automated_delete_process_error.log"
OUTPUT_JSON="${LOCAL_DIR}/${CRAWLER_NAME}_crawler_output.json"



# Start timer
SECONDS=0
cat <<EOF

  STARTING AUTOMATED DELETE PROCESS FOR CRAWLER: ${CRAWLER_NAME} AT ${TIMESTAMP}
  $(date "+DATE: %Y-%m-%d TIME: %H:%M:%S")

EOF

# Step 1: Pull down all metadata files
echo "Downloading metadata files..." | tee -a "${LOG_FILE}" # Display to console and save log
aws s3 cp s3://advana-data-zone/bronze/gamechanger/pdf/ "${LOCAL_DIR}" --exclude="*" --include="*.metadata" --recursive >> "${LOG_FILE}" 2>> "${ERROR_LOG_FILE}" #
# s3://advana-data-zone/bronze/gamechanger/data-pipelines/orchestration/crawlers/cumulative-manifest.json

# Step 2: Filter out metadata files for the desired crawler
echo "Filtering metadata for ${CRAWLER_NAME}..." | tee -a "${LOG_FILE}"
python ./gather_crawler_output.py --crawler "${CRAWLER_NAME}" --input-dir "${LOCAL_DIR}" --output "${OUTPUT_JSON}" >> "${LOG_FILE}" 2>> "${ERROR_LOG_FILE}"

# Step 3: Delete data using delete.sh
echo "Deleting data across s3, postgres, neo4j, and Elasticsearch..." | tee -a "${LOG_FILE}"
bash delete.sh --input "${OUTPUT_JSON}" >> "${LOG_FILE}" 2>> "${ERROR_LOG_FILE}"

# Step 4: Delete from the manifest
echo "Deleting from the manifest..." | tee -a "${LOG_FILE}"
python dataPipelines/scripts/manifest_delete.py --input "${OUTPUT_JSON}" >> "${LOG_FILE}" 2>> "${ERROR_LOG_FILE}"

# Step 5: Upload the updated JSON to a specified S3 path
S3_DESTINATION_PATH="s3://advana-data-zone/bronze/gamechanger/data-pipelines/orchestration/crawlers/cumulative-manifest.json"  # Specify your S3 path here
echo "Uploading the updated JSON to ${S3_DESTINATION_PATH}..." | tee -a "${LOG_FILE}"
aws s3 cp "${OUTPUT_JSON}" "${S3_DESTINATION_PATH}" >> "${LOG_FILE}" 2>> "${ERROR_LOG_FILE}"

# End timer and display elapsed time
cat <<EOF

  FINISHED AUTOMATED DELETE PROCESS FOR CRAWLER: ${CRAWLER_NAME} AT ${TIMESTAMP}
  $(date "+DATE: %Y-%m-%d TIME: %H:%M:%S")

EOF

duration=$SECONDS
echo -e "\nElapsed Time: $(( $SECONDS / 3600 ))h $(( ($SECONDS % 3600)/60 ))m $(($SECONDS % 60))s."
