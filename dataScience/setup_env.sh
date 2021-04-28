#!/bin/bash
if [ -z $1 ]
then 
  echo "No dev environment specified, setting to PROD"
  export ENV_TYPE="PROD"
elif [ "$1" = "DEV" ]
then
  export ENV_TYPE="DEV"
elif [ "$1" = "PROD" ]
then
  export ENV_TYPE="PROD"
elif [ "$1" = "DEVLOCAL" ]
then
  export ENV_TYPE="DEVLOCAL"

fi 

if [ "$ENV_TYPE" = "PROD" ]
then
  echo "Setting up PROD environment"
  export TRANSFORMER_HOST=http://localhost
  export REDIS_HOST=localhost
  export REDIS_PORT=6379
  export GC_ML_HOST=http://localhost
  S3_TRANS_MODEL_PATH="${S3_TRANS_MODEL_PATH:=s3://advana-raw-zone/gamechanger/models/transformers/v5/transformers.tar.gz}"
  export S3_TRANS_MODEL_PATH
  S3_SENT_INDEX_PATH="${S3_SENT_INDEX_PATH:=s3://advana-raw-zone/gamechanger/models/sentence_index/v4/sent_index_20210422.tar.gz}"
  export S3_SENT_INDEX_PATH
  S3_QEXP_PATH="${S3_QEXP_PATH:=s3://advana-raw-zone/gamechanger/models/qexp_model/v3/qexp_20201217.tar.gz}"
  export S3_QEXP_PATH
  S3_TOPICS_PATH="${S3_TOPICS_PATH:=s3://advana-raw-zone/gamechanger/models/topic_model/v1/20210208.tar.gz}"
  export S3_TOPICS_PATH

  export DEV_ENV="PROD"
fi


if [ "$ENV_TYPE" = "DEV" ]
then
  echo "Setting up DEV Docker environment"
  export REDIS_HOST=gc-redis
  export REDIS_PORT=6380
  export GC_ML_HOST=http://host.docker.internal
  S3_TRANS_MODEL_PATH="${S3_TRANS_MODEL_PATH:=s3://advana-raw-zone/gamechanger/models/transformers/v5/transformers.tar.gz}"
  export S3_TRANS_MODEL_PATH
  S3_SENT_INDEX_PATH="${S3_SENT_INDEX_PATH:=s3://advana-raw-zone/gamechanger/models/sentence_index/v4/sent_index_20210422.tar.gz}"
  export S3_SENT_INDEX_PATH
  S3_QEXP_PATH="${S3_QEXP_PATH:=s3://advana-raw-zone/gamechanger/models/qexp_model/v3/qexp_20201217.tar.gz}"
  export S3_QEXP_PATH

  S3_TOPICS_PATH="${S3_TOPICS_PATH:=s3://advana-raw-zone/gamechanger/models/topic_model/v1/20210208.tar.gz}"
  export S3_TOPICS_PATH

  if [ -z "$AWS_PROFILE" ]
  then
      echo "\$AWS_PROFILE is empty"
      unset AWS_PROFILE
  fi
  if [ -z "$AWS_DEFAULT_PROFILE" ]
  then
      echo "\$AWS_DEFAULT_PROFILE is empty"
      unset AWS_DEFAULT_PROFILE
  fi
  export DEV_ENV="DEV"
  export PULL_MODELS="latest"
  export MLFLOW_TRACKING_URI="http://${MLFLOW_HOST}:5050/"
fi

if [ "$ENV_TYPE" = "DEVLOCAL" ]
then
  echo "Setting up DEV environment"
  export REDIS_HOST=localhost
  export REDIS_PORT=6380
  export GC_ML_HOST=http://localhost
  S3_TRANS_MODEL_PATH="${S3_TRANS_MODEL_PATH:=s3://advana-raw-zone/gamechanger/models/transformers/v5/transformers.tar.gz}"
  export S3_TRANS_MODEL_PATH
  S3_SENT_INDEX_PATH="${S3_SENT_INDEX_PATH:=s3://advana-raw-zone/gamechanger/models/sentence_index/v2/sent_index_20210223.tar.gz}"
  export S3_SENT_INDEX_PATH

  export DEV_ENV="DEVLOCAL"
fi

echo "ENVIRONMENT SET: $DEV_ENV "
echo " * AWS SETTING: $DEV_ENV "
echo " * TRANSFORMER HOSTNAME: $TRANSFORMER_HOST "
echo " * REDIS HOST: $REDIS_HOST "
echo " * FLASK HOST: $GC_ML_HOST "
echo " * REDIS PORT: $REDIS_PORT "
echo " * PULL MODELS: $PULL_MODELS "
echo " * GC_ML_API_MODEL_NAME: $GC_ML_API_MODEL_NAME "
echo " * S3_TRANS_MODEL_PATH: $S3_TRANS_MODEL_PATH"
echo " * S3_SENT_INDEX_PATH: $S3_SENT_INDEX_PATH"
echo " * S3_QEXP_PATH: $S3_QEXP_PATH"
echo " * S3_TOPICS_PATH: $S3_TOPICS_PATH"

