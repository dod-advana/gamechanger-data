:: Setting up variables to run the repo configuration
set "SCRIPT_PARENT_DIR=%~dp0"
set "REPO_DIR=%SCRIPT_PARENT_DIR%\.."

set "PYTHONPATH=%REPO_DIR%"

:: Check for the case that we're running this configuration in local to assign python path
if "%DEPLOYMENT_ENV%"=="" set "DEPLOYMENT_ENV=prod"
if "%DEPLOYMENT_ENV%"=="local" (
  set "PYTHON_CMD=python"
) else (
  set "PYTHON_CMD=..\venv\Scripts\python.exe"  :: path to python executable, adjust if necessary
)
set "AWS_CMD=aws"
set "S3_BUCKET_NAME=advana-data-zone"
set "APP_CONFIG_NAME=%DEPLOYMENT_ENV%"
set "ES_CONFIG_NAME=%DEPLOYMENT_ENV%"
set "APP_CONFIG_LOCAL_PATH=%REPO_DIR%\configuration\app-config\%APP_CONFIG_NAME%.json"
set "GAMECHANGERML_PKG_DIR=%REPO_DIR%\var\gamechanger-ml"
set "TOPIC_MODEL_LOCAL_DIR=%GAMECHANGERML_PKG_DIR%\gamechangerml\models\topic_model_20221129162954\models"
set "TOPIC_MODEL_SCRIPT_LOCAL_DIR=%GAMECHANGERML_PKG_DIR%\gamechangerml\models\topic_model_20221129162954\"

:: Setting up s3 path variables depending on if running in prod or running in dev/local
if "%DEPLOYMENT_ENV%"=="prod" (
  set "AWS_DEFAULT_REGION=us-gov-west-1"
  set "APP_CONFIG_S3_PATH=s3://%S3_BUCKET_NAME%/bronze/gamechanger/configuration/app-config/prod.20210416.json"
  set "TOPIC_MODEL_S3_PATH=s3://%S3_BUCKET_NAME%/bronze/gamechanger/models/topic_model/v2/topic_model_20221129162954.tar.gz"
  set "TOPIC_MODEL_SCRIPT_S3_PATH=s3://%S3_BUCKET_NAME%/bronze/gamechanger/models/topic_model/tfidf.py"
) else (
  set "AWS_DEFAULT_REGION=us-east-1"
  set "APP_CONFIG_S3_PATH=s3://%S3_BUCKET_NAME%/bronze/gamechanger/configuration/app-config/dev.20220419.json"
  set "TOPIC_MODEL_S3_PATH=s3://%S3_BUCKET_NAME%/bronze/gamechanger/models/topic_model/v2/topic_model_20221129162954.tar.gz"
  set "TOPIC_MODEL_SCRIPT_S3_PATH=s3://%S3_BUCKET_NAME%/bronze/gamechanger/models/topic_model/tfidf.py"
)

:: Defining the functions to be run in the configuration
call :ensure_gamechangerml_is_installed
call :install_app_config
call :install_topic_models
call :install_topic_model_script
call :configure_repo
call :post_checks

echo Configuration Completed
goto :eof

:ensure_gamechangerml_is_installed
:: This function makes sure that gamechanger-ml repo is cloned/installed
if not exist "%GAMECHANGERML_PKG_DIR%" (
  echo Downloading gamechangerml ...
  git clone https://github.com/dod-advana/gamechanger-ml.git "%GAMECHANGERML_PKG_DIR%"
)
:: running the pip install
%PYTHON_CMD% -m pip freeze | findstr /C:"gamechangerml" >nul || (
  echo Installing gamechangerml in the user packages ...
  %PYTHON_CMD% -m pip install --no-deps -e "%GAMECHANGERML_PKG_DIR%"
)
goto :eof

:install_app_config
:: This function downloads the app-config from s3 if we're not in a local environment
if not "%DEPLOYMENT_ENV%"=="local" (
  if exist "%APP_CONFIG_LOCAL_PATH%" (
    echo Removing old App Config
    del /f "%APP_CONFIG_LOCAL_PATH%"
  )
  echo Fetching new App Config
  %AWS_CMD% s3 cp "%APP_CONFIG_S3_PATH%" "%APP_CONFIG_LOCAL_PATH%"
)
goto :eof

:install_topic_models
:: Downloads the topic model .tar file and extracts it
if exist "%TOPIC_MODEL_LOCAL_DIR%" (
  echo Removing old topic model directory and contents
  rmdir /s /q "%TOPIC_MODEL_LOCAL_DIR%"
)
mkdir "%TOPIC_MODEL_LOCAL_DIR%"
echo Fetching new topic model
:: The following command needs AWS CLI for Windows to support piping, which it may not
%AWS_CMD% s3 cp "%TOPIC_MODEL_S3_PATH%" - | tar -xzf - -C "%TOPIC_MODEL_LOCAL_DIR%" --strip-components=1
goto :eof

:install_topic_model_script
:: This downloads a supplementary .py script
mkdir "%TOPIC_MODEL_SCRIPT_LOCAL_DIR%"
echo Inserting topic model script into gamechangerml
%AWS_CMD% s3 cp "%TOPIC_MODEL_SCRIPT_S3_PATH%" "%TOPIC_MODEL_SCRIPT_LOCAL_DIR%"
goto :eof

:configure_repo
:: Runs the configuration command
echo Initializing default config files
%PYTHON_CMD% -m configuration init %DEPLOYMENT_ENV% --app-config %APP_CONFIG_NAME% --elasticsearch-config %ES_CONFIG_NAME%
goto :eof

:post_checks
:: Checks the connections
if not "%DEPLOYMENT_ENV%"=="local" (
  echo Running post-deploy checks...
  echo Checking connections...
  %PYTHON_CMD% -m configuration check-connections
) else (
  echo Please manually check that the configurations are working properly.
)
goto :eof
