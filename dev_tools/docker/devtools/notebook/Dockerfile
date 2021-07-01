FROM jupyter/minimal-notebook:latest

SHELL [ "/bin/bash", "-c" ]

USER root

#####
## ## Setup Tools & Packages
#####

RUN apt update && apt install -y \
    curl \
    wget \
    vim \
    git \
    postgresql-client \
    jq

RUN curl -LfSo /tmp/awscliv2.zip "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" \
    && unzip -q /tmp/awscliv2.zip -d /opt \
    && /opt/aws/install

#####
## ## Setup User Env
#####

# Switch back to jovyan
USER $NB_UID

## APP VENV & JUPYTER KERNEL
ARG REQUIREMENTS_FILE="/tmp/requirements.txt"
ARG DEV_REQUIREMENTS_FILE="/tmp/dev-requirements.txt"
COPY /dev/requirements/dev-requirements.txt "$DEV_REQUIREMENTS_FILE"
COPY /dev/requirements/gc-venv-current.txt "$REQUIREMENTS_FILE"

ARG APP_VENV_NAME="gc-venv"
RUN conda create -n "$APP_VENV_NAME" python=3.6 ipykernel --yes \
    && conda run -n "$APP_VENV_NAME" python -m ipykernel install --user --name "$APP_VENV_NAME" --display-name "Python (GC-VENV)" \
    && conda run -n "$APP_VENV_NAME" python -m pip install --no-cache-dir --upgrade pip wheel setuptools \
    && conda run -n "$APP_VENV_NAME" python -m pip install --no-cache-dir --no-deps -r "$REQUIREMENTS_FILE" \
    && conda run -n "$APP_VENV_NAME" python -m pip install --no-cache-dir -r "$DEV_REQUIREMENTS_FILE"

## Other Useful Settings
ENV DEV_POSTGRES_HOST='postgres'
ENV DEV_POSTGRES_PORT='5432'
ENV DEV_POSTGRES_DB='dev'
ENV DEV_POSTGRES_USER='postgres'
ENV DEV_POSTGRES_PASSWORD='password'
ENV DEV_S3_HTTP_ENDPOINT='http://s3-server:9000'
ENV DEV_S3_AWS_REGION="us-east-1"
ENV DEV_S3_AWS_ACCESS_KEY="dev-access-key"
ENV DEV_S3_AWS_SECRET_KEY="dev-secret-key"
ENV DEV_S3_SIGNATURE_VERSION="s3v4"

RUN echo insecure > "$HOME/.curlrc" \
    && aws configure set aws_access_key_id ${DEV_S3_AWS_ACCESS_KEY} \
    && aws configure set aws_secret_access_key ${DEV_S3_AWS_SECRET_KEY} \
    && aws configure set default.region ${DEV_S3_AWS_REGION:-us-east-1} \
    && aws configure set default.s3.signature_version ${DEV_S3_SIGNATURE_VERSION} \
    && echo 'aws() { aws --endpoint-url ${DEV_S3_HTTP_ENDPOINT} "$@" ; }' >> "${HOME}/.bashrc" \
    && echo "${DEV_POSTGRES_HOST}:${DEV_POSTGRES_PORT}:${DEV_POSTGRES_DB}:${DEV_POSTGRES_USER}:${DEV_POSTGRES_PASSWORD}" > "${HOME}/.pgpass" \
    && chmod 600 "${HOME}/.pgpass" \
    && conda init bash

WORKDIR $HOME