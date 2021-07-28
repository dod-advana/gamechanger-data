#!/bin/bash
DS_SETUP_PATH="dataScience/setup_env.sh"
ZIP_CACHE="dataScience/transformer_cache.zip"

if [ "$ENV_TYPE" = "TEST" ]
  then
    pytest api_tests.py
elif [ "$ENV_TYPE" = "DEV" ] 
  then
    export GC_ML_HOST="host.docker.internal"
    pytest api_tests.py --junitxml=test_results.xml
fi 
