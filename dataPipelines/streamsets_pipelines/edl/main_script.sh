#!/usr/bin/env bash
set -o errexit
set -o nounset
set -o pipefail

SECONDS=0

#####
## ## SETUP TMP DIR
#####
function setup_tmp_dir() {
  LOCAL_TMP_DIR=$(mktemp -d)
}
setup_tmp_dir # CALLING RIGHT AWAY (to avoid issues with unbound var later)
function echo_tmp_dir_locaton() {
  echo "TEMP DIR IS AT $LOCAL_TMP_DIR"
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
}
trap cleanup_hooks EXIT
#####
## ## SETUP Keytab (used in production)
#####
function init_prod_key_tab() {
  USE_KEYTAB="${USE_KEYTAB:-true}"
  if [[ "$USE_KEYTAB" == "true" ]]; then
   kinit -k -t /etc/security/keytabs/streamsets.keytab "${KRB_NAME}"
  fi
}
#####
## ## Commands to use ES, Solr and AWS
#####
function setup_aws_solr_es_commands() {
  case "$SCRIPT_ENV" in
  dev)
    AWS_CMD="aws"
    SOLR_INDEX_UPDATE_API_ENDPOINT="http://localhost:8983/solr/${INDEX_NAME}/update/json/docs"
    ES_INDEX_UPDATE_API_ENDPOINT="https://${ES_HOST}/${INDEX_NAME}/_doc"
    ;;
  prod)
    AWS_CMD="aws"
     SOLR_INDEX_UPDATE_API_ENDPOINT="https://${SOLR_HOST}:8985/solr/${INDEX_NAME}/update/json/docs"
    ES_INDEX_UPDATE_API_ENDPOINT="https://${ES_HOST}/${INDEX_NAME}/_doc"
    ;;
  docker)
    AWS_CMD="aws --endpoint-url http://localstack:4572"
    SOLR_INDEX_UPDATE_API_ENDPOINT="http://solr:8984/solr/${INDEX_NAME}/update/json/docs"
    ES_INDEX_UPDATE_API_ENDPOINT="http://elasticsearch:9200/${INDEX_NAME}/_doc"
    ;;
  *)
    echo >&2 "Must set SCRIPT_ENV = (docker|dev|test)"
    exit 2
    ;;
  esac
  echo "Using AWS: $AWS_CMD"
  echo "Solr Update URL: $SOLR_INDEX_UPDATE_API_ENDPOINT"
  echo "ES Update URL: $ES_INDEX_UPDATE_API_ENDPOINT"
}
#####
## ## S3/HDFS ENV Vars
#####
function setup_s3_vars_and_dirs() {
  S3_GAMECHANGER_PATH="advana-data-zone/bronze/gamechanger"
  # pdf/json
  S3_GC_PDF_PATH="$S3_GAMECHANGER_PATH/pdf"
  
  if [ "$INDEX_TYPE" == "es" ]; then
    S3_GC_JSON_PATH="$S3_GAMECHANGER_PATH/json_es"
  else
      echo "----- Solr Indexing ------"
      S3_GC_JSON_PATH="$S3_GAMECHANGER_PATH/json"
  fi
  S3_GC_JSON_PATH="$S3_GAMECHANGER_PATH/json"
  S3_GC_JSON_FAIL_SOLR_PATH="$S3_GAMECHANGER_PATH/json_fail_index_solr"
  echo "S3 GC Path PDF: $S3_GC_PDF_PATH"
  echo "S3 GC Path JSON: $S3_GC_JSON_PATH"
  echo "S3 GC Path fail index JSON: $S3_GC_JSON_FAIL_SOLR_PATH"
}

function update_solr_index() {
  local RESPONSE_HEADER="responseHeader"
  find "$LOCAL_TMP_DIR/output/" -name "*.json" -print0 | while IFS= read -r -d '' file; do
      echo "file = $file"
    local _test=$(curl --negotiate -u : -b ~/cookiejar.txt -c ~/cookiejar.txt --show-error --fail -s -k -X POST -H 'Content-Type: application/json' ${SOLR_INDEX_UPDATE_API_ENDPOINT} --data-binary "@$file")
    echo "----- Message: $_test"
    if [[ "$_test" == *"$RESPONSE_HEADER"* ]]; then
      echo "File $file add to Solr $INDEX_NAME"
    else
      echo "Failed to index $file adding file to advana-data-zone/bronze/gamechanger/json_failed_add_solr"
      export AWS_DEFAULT_REGION=$AWS_REGION
      $AWS_CMD s3 cp "$file" "s3://$S3_GC_JSON_FAIL_SOLR_PATH/$_filename.json"
    fi
  done
}

#####
## ## Elasticsearxh Index Update Vars/Functions
#####
function update_es_index() {
  local RESPONSE_HEADER="result"
  find "$LOCAL_TMP_DIR/output/" -name "*.json" -print0 | while IFS= read -r -d '' file; do
      echo "file = $file"
    _filename=$(basename "$file" .json)
    _id=$(echo -n "$_filename" | md5sum | cut -d' ' -f1)
    if [ -z "$PASSWORD" ]; then
       _test=$(curl --silent  --show-error  -H "Content-Type: application/json" -XPOST "${ES_INDEX_UPDATE_API_ENDPOINT}/${_id}" --data-binary "@$file")
     else
       _test=$(curl --silent  --show-error --fail  -H "Content-Type: application/json" -u $USERNAME:$PASSWORD -XPOST "${ES_INDEX_UPDATE_API_ENDPOINT}/${_id}" --data-binary "@$file")
       
      fi
     echo $_test
    if [[ "$_test" == *"$RESPONSE_HEADER"* ]]; then
        echo "File $file add to Elasticsearch $INDEX_NAME"
    else
        echo "Failed to index $file adding file to advana-data-zone/bronze/gamechanger/json_failed_add_solr"
        export AWS_DEFAULT_REGION=$AWS_REGION
        $AWS_CMD s3 cp "$file" "s3://$S3_GC_JSON_FAIL_SOLR_PATH/$_filename.json"
    fi
  done
}

#####
## ## Update S3/Functions
#####
function update_s3_pdf() {
  find $LOCAL_TMP_DIR/output/ -name "*.pdf" -print0 | while IFS= read -r -d '' file; do
    echo "file = $file";
    name=$(basename "$file")
    $AWS_CMD s3 cp "${file}" "s3://$S3_GC_PDF_PATH/${name}"
    cat "${file}" | hdfs dfs -put -f - "/data_zones/raw_zone/gamechanger/${name}"
  done
}

function update_s3_json() {
  find $LOCAL_TMP_DIR/output/ -name "*.json" -print0 | while IFS= read -r -d '' file; do
    echo "file = $file";
    name=$(basename "$file")
    $AWS_CMD s3 cp "${file}" "s3://$S3_GC_JSON_PATH/${name}"
  done
}



echo "***************************** Start *****************************"

init_prod_key_tab
echo_tmp_dir_locaton
setup_aws_solr_es_commands
setup_s3_vars_and_dirs

echo $unzip_dir
hdfs dfs -get $unzip_dir $LOCAL_TMP_DIR/json.zip
unzip $LOCAL_TMP_DIR/json.zip -d $LOCAL_TMP_DIR/output


update_s3_pdf
update_s3_json

# update index
if [ "$INDEX_TYPE" == "es" ]; then
    echo "----- Elasticsearch Indexing ------"
    update_es_index
else
    echo "----- Solr Indexing ------"
    update_solr_index
fi

duration=$SECONDS
echo "$(($duration / 60)) minutes and $(($duration % 60)) seconds elapsed."
echo "***************************** Done *****************************"
