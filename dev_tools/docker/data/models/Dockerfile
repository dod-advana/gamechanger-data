ARG BASE_IMAGE='centos:7'
FROM $BASE_IMAGE

#####
## ## CMD Prereqs
#####

## running as root
USER root

## shell for RUN cmd purposes
SHELL ["/bin/bash", "-c"]

# LOCALE (important for python, etc.)
RUN localedef -i en_US -f UTF-8 en_US.UTF-8
ENV LANG="en_US.UTF-8" \
    LANGUAGE="en_US.UTF-8" \
    LC_ALL="en_US.UTF-8"

# Some tools
RUN \
    yum update -y \
    && yum install -y \
        wget \
        bzip2 \
        zip \
        unzip \
    && yum clean all \
    && rm -rf /var/cache/yum \
    \
    && curl -LfSo /tmp/awscliv2.zip "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" \
    && unzip -q /tmp/awscliv2.zip -d /opt \
    && /opt/aws/install \
    && rm -f /tmp/awscliv2.zip

#####
## ## ML Data Setup
#####

## MODEL SETTINGS (prefixes always end with /)
ARG TOPIC_MODEL_S3_PREFIX_URL="s3://advana-data-zone/bronze/gamechanger/models/topic_model/v1/"
ARG TRANSFORMER_MODEL_BUNDLE_S3_URL="s3://advana-data-zone/bronze/gamechanger/models/transformers/v5/20210224.tar.gz"
ARG SENTENCE_INDEX_BUNDLE_S3_URL="s3://advana-data-zone/bronze/gamechanger/models/sentence_index/v7/sent_index_20210716.tar.gz"
ARG QEXP_MODEL_S3_PREFIX_URL="s3://advana-data-zone/bronze/gamechanger/models/qexp_model/v3/"
ARG QEXP_MODEL_NAME="qexp_20201217"

## ENV VARS (has to match expected paths for <ds>/models/ to avoid extra configuration of ml-api)
ENV ML_MODELS_DIR="/data/models/"
ENV TOPIC_MODEL_DIR="${ML_MODELS_DIR}/topic_models/"
ENV QEXP_MODEL_DIR="${ML_MODELS_DIR}/${QEXP_MODEL_NAME}"

## Prepare dirs
RUN mkdir -p "$ML_MODELS_DIR" "$TOPIC_MODEL_DIR" "$QEXP_MODEL_DIR"

## Pull models ...
RUN aws s3 cp "$TOPIC_MODEL_S3_PREFIX_URL" "$TOPIC_MODEL_DIR/" --recursive
RUN aws s3 cp "$QEXP_MODEL_S3_PREFIX_URL" "$QEXP_MODEL_DIR/" --recursive
RUN aws s3 cp "$TRANSFORMER_MODEL_BUNDLE_S3_URL" - | tar -xzf - --exclude="*/.git/*" -C "$ML_MODELS_DIR"
RUN aws s3 cp "$SENTENCE_INDEX_BUNDLE_S3_URL" - | tar -xzf - --exclude="*/.git/*" -C "$ML_MODELS_DIR"

# Not meant to run normally, use as part of multi-stage build, to copy data from, or to prime a shared volume
ENTRYPOINT "/bin/true"