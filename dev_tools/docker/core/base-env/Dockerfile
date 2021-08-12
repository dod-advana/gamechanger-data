ARG MODEL_DATA_IMAGE="gamechanger/data/models:latest"
ARG BASE_OS_IMAGE='centos:7'

FROM $MODEL_DATA_IMAGE as models
ARG BASE_OS_IMAGE

FROM $BASE_OS_IMAGE
## running as root
USER root

## shell for RUN cmd purposes
SHELL ["/bin/bash", "-c"]

# LOCALE (important for python, etc.)
RUN localedef -i en_US -f UTF-8 en_US.UTF-8

ENV LANG="en_US.UTF-8"
ENV LANGUAGE="en_US.UTF-8"
ENV LC_ALL="en_US.UTF-8"

#####
## ## SYS Package Setup
#####

# Python3 and Env Prereqs
RUN yum update -y \
    && yum group install -y "Development Tools" \
    && yum install -y \
        wget \
        postgresql.x86_64 \
        postgresql-devel.x86_64 \
        python3.x86_64 \
        python3-devel.x86_64 \
        python3-pip.noarch \
        vim \
        https://corretto.aws/downloads/latest/amazon-corretto-8-x64-linux-jdk.rpm \
        bzip2 \
        glibc.i686 \
        sudo \
    && yum clean all \
    && rm -rf /var/cache/yum

# Update base python setup packages
RUN pip3 install --upgrade pip wheel setuptools

# AWS CLI
RUN curl -LfSo /tmp/awscliv2.zip "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" \
    && unzip -q /tmp/awscliv2.zip -d /opt \
    && /opt/aws/install

# passless sudo to make things easier
RUN sed -ri '/^\s*%wheel/c\%wheel ALL=(ALL) NOPASSWD: ALL' /etc/sudoers

# JDK
ENV JAVA_HOME="/usr/lib/jvm/java-1.8.0-amazon-corretto"

#####
## ## Python Package Env Prereqs
#####

RUN yum install -y \
        python-cffi \
        libffi-devel \
        cairo \
        pango \
        gdk-pixbuf2 \
        ghostscript \
        qpdf \
        libtiff-devel \
        libjpeg-turbo-devel \
        libpng-devel \
        cairo-devel \
        cairomm-devel \
        pango-devel \
        pangomm-devel \
    && yum clean all \
    && rm -rf /var/cache/yum


#####
## ## Other packages (for OCR)
#####

RUN echo /usr/local/lib > /etc/ld.so.conf.d/usr-local.conf
RUN git clone --depth 1 --branch 1.79.0 --single-branch https://github.com/DanBloomberg/leptonica.git /tmp/leptonica \
    && cd /tmp/leptonica \
    && ./autogen.sh \
    && ./configure \
    && make -j$(nproc) \
    && make install \
    && ldconfig \
    && cd - \
    && rm -rf /tmp/leptonica
RUN git clone --depth 1 --branch release-60-3 --single-branch https://github.com/unicode-org/icu.git /tmp/icu \
    && cd /tmp/icu/icu4c/source \
    && ./runConfigureICU Linux \
    && make -j$(nproc) \
    && make install \
    && ldconfig \
    && cd - \
    && rm -rf /tmp/icu
RUN git clone --depth 1 --branch 4.1.1 --single-branch https://github.com/tesseract-ocr/tesseract.git  /tmp/tesseract \
    && cd /tmp/tesseract \
    && ./autogen.sh \
    && PKG_CONFIG_PATH=/usr/local/lib/pkgconfig/ ./configure \
    && make -j$(nproc) \
    && make install \
    && make -j$(nproc) training \
    && make training-install \
    && ldconfig \
    && cd - \
    && rm -rf /tmp/tesseract \
    && wget https://github.com/tesseract-ocr/tessdata_best/raw/4.1.0/eng.traineddata -P /usr/local/share/tessdata/ \
    && wget https://github.com/tesseract-ocr/tessdata_best/raw/4.1.0/osd.traineddata -P /usr/local/share/tessdata/

#####
## ## Python Package Setup
#####

ARG BUILD_CTX_COMPREHENSIVE_REQS="./dev_tools/requirements/gc-venv-current.txt"
ARG LOCAL_REQS="/tmp/gc-venv-reqs.txt"
COPY "$BUILD_CTX_COMPREHENSIVE_REQS" "$LOCAL_REQS"

ENV BASE_APP_VENV_PATH="/opt/gc-venv"
RUN python3 -m venv "${BASE_APP_VENV_PATH}" --copies
RUN "${BASE_APP_VENV_PATH}/bin/pip" install --no-cache-dir --upgrade pip setuptools wheel
RUN "${BASE_APP_VENV_PATH}/bin/pip" install --no-cache-dir --no-deps -r "$LOCAL_REQS"


#####
## ## ML Models
#####

RUN mkdir /data
COPY --from=models /data/models /data/models
ENV GC_ML_DEFAULT_TOPIC_MODEL_DIR=/data/models/topic_models
ENV GC_ML_API_MODEL_PARENT_DIR=/data/models

#####
## ## Entrypoint
#####

# same as for centos image (bash)