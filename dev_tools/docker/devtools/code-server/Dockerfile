####
 ####
  #### VS CODE SERVER - GC EDITION
 ####
####

ARG BASE_IMAGE='centos:7'
FROM $BASE_IMAGE

## running as root
USER root

## shell for RUN cmd purposes
SHELL ["/bin/bash", "-c"]

#####
## ## Base Dev Package Setup
#####

# LOCALE (important for python, etc.)
RUN localedef -i en_US -f UTF-8 en_US.UTF-8

ENV LANG="en_US.UTF-8" \
    LANGUAGE="en_US.UTF-8" \
    LC_CTYPE="en_US.UTF-8" \
    LC_NUMERIC="en_US.UTF-8" \
    LC_TIME="en_US.UTF-8" \
    LC_COLLATE="en_US.UTF-8" \
    LC_MONETARY="en_US.UTF-8" \
    LC_MESSAGES="en_US.UTF-8" \
    LC_PAPER="en_US.UTF-8" \
    LC_NAME="en_US.UTF-8" \
    LC_ADDRESS="en_US.UTF-8" \
    LC_TELEPHONE="en_US.UTF-8"\
    LC_MEASUREMENT="en_US.UTF-8" \
    LC_IDENTIFICATION="en_US.UTF-8" \
    LC_ALL="en_US.UTF-8"

# Install EPEL & IUS repos
RUN \
    curl -k -o /tmp/ius.rpm https://repo.ius.io/ius-release-el7.rpm \
    && curl -k -o /tmp/epel.rpm https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm \
    && yum install -y /tmp/ius.rpm \
    && yum install -y /tmp/epel.rpm \
    && rm -f /tmp/ius.rpm /tmp/epel.rpm

# This is a dev img, we want the man pages
RUN sed -i '/tsflags=nodocs/d' /etc/yum.conf
RUN yum install -y man-db man-pages \
    && yum reinstall -y shadow-utils \
    && mandb

# Various tools/prereqs
RUN yum update -y \
    && yum group install -y "Development Tools" \
    && yum remove -y git \
    && yum install -y git224 \
    && yum install -y \
        wget \
        postgresql.x86_64 \
        postgresql-devel.x86_64 \
        python3.x86_64 \
        python3-devel.x86_64 \
        python3-pip.noarch \
        rpmdevtools.noarch \
        tmux \
        screen \
        openssl \
        openssh \
        vim \
        bzip2 \
        glibc.i686 \
        jq \
        zip \
        unzip \
        which \
        sudo \
        https://corretto.aws/downloads/latest/amazon-corretto-11-x64-linux-jdk.rpm \
    && yum clean all \
    && rm -rf /var/cache/yum \
    && mandb

# JDK 11
ENV JAVA_HOME="/usr/lib/jvm/java"

# AWS CLI
RUN curl -LfSo /tmp/awscliv2.zip "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" \
    && unzip -q /tmp/awscliv2.zip -d /opt \
    && /opt/aws/install \
    && rm -f /tmp/awscliv2.zip \
    && mandb

# Git LFS extension
RUN curl -s https://packagecloud.io/install/repositories/github/git-lfs/script.rpm.sh | sudo bash

#####
## ## Web & Crawler Tools
#####

# Node JS
RUN curl -sL https://rpm.nodesource.com/setup_14.x | bash -

# chrome browser
COPY dev/docker/gc_code_server/google-chrome.repo /etc/yum.repos.d/google-chrome.repo
RUN \
    curl https://dl-ssl.google.com/linux/linux_signing_key.pub -o /tmp/google_key.pub \
        && rpm --import /tmp/google_key.pub \
        && rm /tmp/google_key.pub \
    && yum install google-chrome-stable -y \
    && yum clean all \
    && rm -rf /var/cache/yum \
    && mandb

# chrome driver
RUN \
    wget -O /tmp/chromedriver.zip \
        https://chromedriver.storage.googleapis.com/$(curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE)/chromedriver_linux64.zip \
    && unzip /tmp/chromedriver.zip chromedriver -d /usr/local/bin/ \
    && chmod +x /usr/local/bin/chromedriver \
    && rm /tmp/chromedriver.zip

#####
## ## Container Utils
#####

# installing podman
RUN curl -fsSL \
        -o /etc/yum.repos.d/devel:kubic:libcontainers:stable.repo \
        https://download.opensuse.org/repositories/devel:/kubic:/libcontainers:/stable/CentOS_7/devel:kubic:libcontainers:stable.repo \
    && yum -y install podman \
    && mandb

# installing docker utils
RUN yum-config-manager \
        --add-repo \
        https://download.docker.com/linux/centos/docker-ce.repo \
    && yum install -y docker-ce-cli \
    && mandb

# installing docker compose
RUN curl -fsSL \
        -o /usr/local/bin/docker-compose \
        "https://github.com/docker/compose/releases/download/1.27.4/docker-compose-$(uname -s)-$(uname -m)" \
    && chmod +x /usr/local/bin/docker-compose

# installing kubectl
RUN KUBECTL_RELEASE=$(curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt) \
     && curl -fsSL \
        -o /usr/local/bin/kubectl \
        "https://storage.googleapis.com/kubernetes-release/release/$KUBECTL_RELEASE/bin/linux/amd64/kubectl" \
     && chmod +x /usr/local/bin/kubectl

#####
## ## VS CODE SERVER SETUP
#####

ENV CODE_SERVER_UID=1000
ENV CODE_SERVER_GID=1000
ENV CODE_SERVER_USER=coder
ENV CODE_SERVER_GROUP=coder

RUN groupadd -g $CODE_SERVER_GID $CODE_SERVER_GROUP && \
    useradd -u $CODE_SERVER_UID -g $CODE_SERVER_GROUP -d /home/$CODE_SERVER_USER -s /bin/bash $CODE_SERVER_USER \
    && echo "$CODE_SERVER_USER ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers.d/nopasswd

# script to fix uid's in mounted dirs
RUN curl -fsSL "https://github.com/boxboat/fixuid/releases/download/v0.5/fixuid-0.5-linux-amd64.tar.gz" | tar -C /usr/local/bin -xzf - \
    && chown root:root /usr/local/bin/fixuid \
    && chmod 4755 /usr/local/bin/fixuid \
    && mkdir -p /etc/fixuid \
    && printf "user: ${CODE_SERVER_USER}\ngroup: ${CODE_SERVER_GROUP}\n" > /etc/fixuid/config.yml

# and finally... installing code-server
RUN yum install -y \
        https://github.com/cdr/code-server/releases/download/v3.7.4/code-server-3.7.4-amd64.rpm \
    && yum clean all \
    && rm -rf /var/cache/yum

# process reaper - to slay zombie children of vs-code server
ENV TINI_VERSION v0.19.0
ADD https://github.com/krallin/tini/releases/download/${TINI_VERSION}/tini /usr/bin/tini
RUN chmod +x /usr/bin/tini

# just to make sure bash shell is always the default
RUN chsh -s /bin/bash
ENV SHELL=/bin/bash

#####
## ## DE env prereqs
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
    && yum clean all \
    && rm -rf /var/cache/yum \
    && mandb


ARG LEPTONICA_RPM_S3_URL="s3://advana-data-zone/bronze/gamechanger/package-approvals/ocr-20201106/leptonica-1.79.0-1.el7.x86_64.rpm"
ARG TESSERACT_RPM_S3_URL="s3://advana-data-zone/bronze/gamechanger/package-approvals/ocr-20201106/tesseract-4.1.1-1.el7.x86_64.rpm"
RUN \
    mkdir /tmp/rpm-staging \
    && aws s3 cp "$LEPTONICA_RPM_S3_URL" /tmp/rpm-staging/leptonica.rpm \
    && rpm -i /tmp/rpm-staging/leptonica.rpm \
    && aws s3 cp "$TESSERACT_RPM_S3_URL" /tmp/rpm-staging/tesseract.rpm \
    && rpm -i /tmp/rpm-staging/tesseract.rpm \
    && rm -rf /tmp/rpm-staging

#####
## ## DS env prereqs
#####

ARG TRANSFORMER_CACHE_S3_URL="s3://data-tools-s3-2/transformer_models_v3/transformer_cache.zip"
RUN \
    aws s3 cp "$TRANSFORMER_CACHE_S3_URL" /tmp/cache.zip \
    && unzip /tmp/cache.zip -d / \
    && rm -f /tmp/cache.zip

ENV TRANSFORMER_CACHE=/transformer_cache/.cache/torch/transformers/

#####
## ## Code Server Plugins
#####

# This way, if someone sets $DOCKER_USER, docker-exec will still work as
# the uid will remain the same. note: only relevant if -u isn't passed to
# docker-run. Also, code server extensions get installed into user dir, so...
USER $CODE_SERVER_UID

RUN \
       code-server --install-extension ms-python.python \
    && code-server --install-extension littlefoxteam.vscode-python-test-adapter \
    && code-server --install-extension donjayamanne.python-extension-pack \
    && code-server --install-extension ms-toolsai.jupyter \
    && code-server --install-extension pkief.material-icon-theme \
    && code-server --install-extension alefragnani.project-manager \
    && code-server --install-extension ms-azuretools.vscode-docker \
    && code-server --install-extension ms-kubernetes-tools.vscode-kubernetes-tools

#####
## ## Comprehensive GC Python Env
#####

USER root

COPY "./dev/requirements/gc-venv-current.txt" "/tmp/gc-venv-reqs.txt"

# Update base python setup packages
RUN pip3 install --no-cache-dir --upgrade pip wheel setuptools \
    && pip3 install --no-cache-dir --no-deps -r "/tmp/gc-venv-reqs.txt"

#####
## ## Startup & Entrypoint Config
#####

USER $CODE_SERVER_UID

# additional env var, to setup git credentials
## e.g. VAR=https://<bitbucket-username>:<bitbucket-token>@bitbucket.di2e.net
ENV BITBUCKET_USER_CREDENTIALS=""

# install entrypoint
COPY dev/docker/devtools/code-server/entrypoint.sh /usr/bin/entrypoint.sh

EXPOSE 8080

ENV USER=${CODE_SERVER_USER}
WORKDIR /home/${CODE_SERVER_USER}

ENTRYPOINT ["/usr/bin/entrypoint.sh", "--disable-telemetry", "--disable-update-check", "--bind-addr", "0.0.0.0:8080", "."]