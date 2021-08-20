#!/usr/bin/env bash
set -o errexit
set -o nounset
set -o pipefail
echo "PROJECTS: ${projects}"
echo "filename: ${filename}"
SECONDS=0

# always set in stage params
SCRIPT_ENV=${SCRIPT_ENV:-dev}
# Check basic params
case "$SCRIPT_ENV" in
dev)
  echo "RUNNING IN DEV ENV"
  ;;
prod)
  echo "RUNNING IN PROD ENV"
  ;;
docker)
  echo "RUNNING IN DOCKER ENV"
  ;;
*)
  echo >&2 "Must set SCRIPT_ENV = (prod|dev|docker)"
  exit 2
  ;;
esac


#####
## ## Commands to use Python and AWS
#####
function setup_aws_and_python_exec_commands() {
  case "$SCRIPT_ENV" in
  dev)
    AWS_CMD="aws"
    ES_INDEX_UPDATE_API_ENDPOINT="${ES_HOST}/${INDEX_NAME}/_doc"
    ;;
  prod)
    AWS_CMD="aws"
    ES_INDEX_UPDATE_API_ENDPOINT="${ES_HOST}/${INDEX_NAME}/_doc"
    ;;
  docker)
    AWS_CMD="aws --endpoint-url http://localstack:4572"
    ES_INDEX_UPDATE_API_ENDPOINT="http://elasticsearch:9200/${INDEX_NAME}/_doc"
    ;;
  *)
    echo >&2 "Must set SCRIPT_ENV = (prod|dev|test)"
    exit 2
    ;;
  esac
  echo "Using AWS: $AWS_CMD"
  echo "INDEX_NAME: $INDEX_NAME"
  echo "Elasticsearch Update URL: $ES_INDEX_UPDATE_API_ENDPOINT"
}

#####
## ## S3/HDFS ENV Vars
#####
function setup_s3_vars_and_dirs() {
  S3_GAMECHANGER_PATH="advana-data-zone/gamechanger"
  S3_GC_JSON_PATH="$S3_GAMECHANGER_PATH/json_es"
  S3_GC_JSON_FAIL_SOLR_PATH="$S3_GAMECHANGER_PATH/json_fail_index_solr"
  echo "S3 GC Path JSON: $S3_GC_JSON_PATH"
}



#####
## ## Elasticsearch Index Update Vars/Functions
#####
function clone_to_s3() {
  local RESPONSE_HEADER="result"
  timestamp=$(sed 's/.\{5\}$//' <<< $(date --iso-8601=seconds))
  replace='%20'
  input_file='/apps/webapp/ExternalDataLoadUploads/${filename}'
  input_file_fix=${input_file//' '/$replace}
  s3_file='s3://advana-data-zone/bronze/gamechanger/project/$projects/uploads/$timestamp/${filename}'
  s3_file_fix=${s3_file//' '/$replace}
  ssh -t -i /tmp/repo/gamechanger/api/ssl/uot.pem centos@"${DEV_HDFS_HOST}" "hdfs dfs -cat '${input_file_fix}' | /home/centos/.local/bin/aws s3 cp - '${s3_file_fix}'"
}


echo "***************************** Start *****************************"
setup_aws_and_python_exec_commands
setup_s3_vars_and_dirs

# Update Elaticsearch with jsons
clone_to_s3


duration=$SECONDS
echo "$(($duration / 60)) minutes and $(($duration % 60)) seconds elapsed."
echo "***************************** Done *****************************"