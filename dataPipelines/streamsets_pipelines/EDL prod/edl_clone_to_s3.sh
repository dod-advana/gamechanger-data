#!/usr/bin/env bash
set -o errexit
set -o nounset
set -o pipefail
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
function kinit_command() {
  if [ "$SCRIPT_ENV" = "prod" ]; then
    kinit -k -t /etc/security/keytabs/streamsets.keytab "${KRB_NAME}"
  fi
}
function setup_aws_and_python_exec_commands() {
  case "$SCRIPT_ENV" in
  dev)
    AWS_CMD="aws"
    export AWS_DEFAULT_REGION="us-east-1"
    ;;
  prod)
    AWS_CMD="aws"
    export AWS_DEFAULT_REGION="us-gov-west-1"
    ;;
  docker)
    AWS_CMD="aws --endpoint-url http://localstack:4572"
    ;;
  *)
    echo >&2 "Must set SCRIPT_ENV = (prod|dev|test)"
    exit 2
    ;;
  esac
  echo "Using AWS: $AWS_CMD"
}



#####
## ## clone to s3
#####
function clone_to_s3() {
  local RESPONSE_HEADER="result"
  timestamp=$(sed 's/.\{5\}$//' <<< $(date --iso-8601=seconds))
  timestamp=$(sed 's/://g' <<< $timestamp)
  echo "input file path: ${INPUT_FILE_PATH}"
  s3_dir="s3a://advana-data-zone/bronze/gamechanger/projects/${PROJECT_NAME}/pdf/"
  replace='%20'
  s3_dir_fixed=${s3_dir//' '/$replace}
  s3_file="s3a://advana-data-zone/bronze/gamechanger/projects/${PROJECT_NAME}/pdf/${FILENAME}"
  s3_file_fixed=${s3_file//' '/$replace}
  INPUT_FILE_PATH_FIX=${INPUT_FILE_PATH//' '/$replace}
  hadoop fs -mkdir -p $s3_dir_fixed
  hadoop distcp "${INPUT_FILE_PATH_FIX}" "${s3_file_fixed}"
}


echo "***************************** Start *****************************"
kinit_command
setup_aws_and_python_exec_commands
clone_to_s3


duration=$SECONDS
echo "$(($duration / 60)) minutes and $(($duration % 60)) seconds elapsed."
echo "***************************** Done *****************************"