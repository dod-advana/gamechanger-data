ARG MODEL_DATA_IMAGE="gamechanger/data/models:latest"
ARG BASE_OS_IMAGE="gamechanger/core/base-env:latest"

###
#### Get ML Assets/Models
#####
FROM $MODEL_DATA_IMAGE AS models
# have to redeclare, so arg doesn't disappear for next build stage
ARG BASE_OS_IMAGE

###
#### App Setup
#####
FROM $BASE_OS_IMAGE

## utility env vars
ENV APP_REPO_DIR=/app
ENV APP_LOG_DIR=/var/log/gamechanger
ENV APP_LOG_FILE="${APP_LOG_DIR}/gamechanger.log"
ENV APP_ENV_DIR="${APP_REPO_DIR}/env"
## app config env vars
ENV GC_ML_API_MODEL_PARENT_DIR="/data/models/"
ENV GC_ML_DEFAULT_TOPIC_MODEL_DIR="/data/models/topic_models"
ENV GC_ML_API_MODEL_NAME="20201217"

# Setup expected dirs/files
RUN mkdir -p \
        "$APP_REPO_DIR" \
        "$APP_LOG_DIR" \
        "$APP_ENV_DIR" \
        "$GC_ML_API_MODEL_PARENT_DIR" \
    && touch "$APP_LOG_FILE"
# set as workdir
WORKDIR "${APP_REPO_DIR}"

# copy ML assets/models
RUN mkdir -p "/data"
COPY --from=models "/data/models" "$GC_ML_API_MODEL_PARENT_DIR"

# setup app dir
COPY . "${APP_REPO_DIR}"

# for dev purposes (if packages vary from base image)
ARG REINSTALL_REQUIREMENTS="no"
ENV BASE_APP_VENV_PATH="/opt/gc-venv"
ARG API_REQUIREMENTS_FILE="${APP_REPO_DIR}/dev/requirements/gc-venv-current.txt"
RUN if [[ "$REINSTALL_REQUIREMENTS" -eq "yes" ]]; \
        then "${BASE_APP_VENV_PATH}/bin/pip" install --no-cache-dir --no-deps -r "$API_REQUIREMENTS_FILE" ; \
    fi

#####
## ## Entrypoint
#####

EXPOSE 5000

ENTRYPOINT ["/bin/bash", "${APP_REPO_DIR}/dataScience/api/fastapi/startFast.sh"]