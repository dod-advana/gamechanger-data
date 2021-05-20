#!/bin/bash
DS_SETUP_PATH="dataScience/setup_env.sh"
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

if [ -z $2 ]
then
  echo "No option to skip downloads setting default to download"
  if [ -z "$DOWNLOAD_DEP" ]
  then
    DOWNLOAD_DEP=true
  fi
elif [ "$2" = true ]
then
  DOWNLOAD_DEP=true
elif [ "$2" = false ]
then
  DOWNLOAD_DEP=false
fi
echo $DOWNLOAD_DEP
if [ "$ENV_TYPE" = "PROD" ]
  then
    source ./dataScience/setup_env.sh PROD
    echo "Activating venv"
    source /opt/gc-venv-current/bin/activate
    if [ "$DOWNLOAD_DEP" = true ]
    then
      echo "Attempting to download models from s3"
      echo "$GC_ML_API_MODEL_NAME - if this is blank it will default"
      echo "Attempting to download transformer cache and sentence index from s3"
      source ./dataScience/scripts/download_dependencies.sh
    fi
    echo "Starting gunicorn workers for API"
    gunicorn dataScience.api.fastapi.mlapp:app --bind 0.0.0.0:5000 --workers 1 --graceful-timeout 900 --timeout 1200 -k uvicorn.workers.UvicornWorker --log-level debug
elif [ "$ENV_TYPE" = "DEV" ] 
then
    source ./dataScience/setup_env.sh DEV
    source ../../venv/bin/activate  
    if [ "$DOWNLOAD_DEP" = true ]
    then
      echo "Attempting to download models from s3"
      echo "$GC_ML_API_MODEL_NAME - if this is blank it will default"
      echo "Attempting to download transformer cache and sentence index from s3"
      source ./dataScience/scripts/download_dependencies.sh
    fi
    gunicorn dataScience.api.fastapi.mlapp:app --bind 0.0.0.0:5000 --workers 1 --graceful-timeout 1000 --timeout 1200 --keep-alive 30 -k uvicorn.workers.UvicornWorker --log-level debug
    #uvicorn dataScience.api.fastapi.mlapp:app --host 0.0.0.0 --port 5000 --workers 1 --log-level debug --timeout-keep-alive 240
elif [ "$ENV_TYPE" = "DEVLOCAL" ] 
then
    source ./dataScience/setup_env.sh DEVLOCAL
    source ../../venv/bin/activate  
    echo "Attempting to download models from s3"
    echo "$GC_ML_API_MODEL_NAME - if this is blank it will default"
    #python -m dataScience.api.getInitModels
    echo "Attempting to download transformer cache and sentence index from s3"
    #source ./dataScience/scripts/download_dependencies.sh
    gunicorn dataScience.api.fastapi.mlapp:app --bind 0.0.0.0:5000 --workers 1 --graceful-timeout 900 --timeout 1600 -k uvicorn.workers.UvicornWorker --log-level debug --reload
 
fi 
