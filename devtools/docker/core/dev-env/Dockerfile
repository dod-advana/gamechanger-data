ARG BASE_IMAGE='gamechanger/core/base-env:latest'
FROM $BASE_IMAGE

#####
## ## Dev Python Package Setup
#####

ARG BUILD_CTX_COMPREHENSIVE_REQS="./dev/requirements/dev-requirements.txt"
ARG LOCAL_REQS="/tmp/dev-reqs.txt"
COPY "$BUILD_CTX_COMPREHENSIVE_REQS" "$LOCAL_REQS"

ENV BASE_APP_VENV_PATH="/opt/gc-venv"
RUN "${BASE_APP_VENV_PATH}/bin/pip" install --no-cache-dir -r "$LOCAL_REQS"