#!/bin/bash
S3_TRANS_MODEL_PATH="s3://data-tools-s3-2/transformer_models_v3/transformer_cache"

if [ "$1" = "WRITE" ]
then
  echo "Writing to ${S3_TRANS_MODEL_PATH}"
  
  aws s3 cp --recursive gamechangerml/transformer_cache/ $S3_TRANS_MODEL_PATH
elif [ "$1" = "READ" ]
then
  echo "Reading from ${S3_TRANS_MODEL_PATH}"
  aws s3 cp $S3_TRANS_MODEL_PATH gamechangerml/transformer_cache/ --recursive
fi
