FROM --platform=x86_64 centos:centos7.9.2009

USER root

ARG SCL_PYTHON_VERSION="38"

RUN \
      rpm --import https://dl.fedoraproject.org/pub/epel/RPM-GPG-KEY-EPEL \
  &&  rpm --import https://dl.fedoraproject.org/pub/epel/RPM-GPG-KEY-EPEL-7 \
  &&  yum install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm \
  &&  rpm --import https://repo.ius.io/RPM-GPG-KEY-IUS-7 \
  &&  yum install -y https://repo.ius.io/ius-release-el7.rpm

# Basic builder packages + some extras
RUN \
      yum install -y \
        centos-release-scl \
  &&  yum install -y \
        git224 \
        devtoolset-10 \
        "rh-python${SCL_PYTHON_VERSION}" \
        "rh-python${SCL_PYTHON_VERSION}-scldevel" \
  &&  yum install -y https://corretto.aws/downloads/latest/amazon-corretto-11-x64-linux-jdk.rpm \
  &&  yum install -y \
        rpm-build \
        rpm-sign \
        redhat-rpm-config \
        rpmlint \
        bzip2 \
        tar \
        zip \
        unzip \
        gzip \
        zlib \
        zlib-devel \
        vim \
        which \
        make \
        automake \
        autoconf \
        libtool \
        diffutils \
  &&  yum clean all -y

# Make sure all apps can find java ...
ENV JAVA_HOME=/etc/alternatives/java_sdk

# Install GIT LFS
RUN \
      curl -L -o /tmp/gitlfs.rpm https://packagecloud.io/github/git-lfs/packages/el/7/git-lfs-3.0.1-1.el7.x86_64.rpm/download \
  &&  yum install -y /tmp/gitlfs.rpm \
  &&  rm -f /tmp/gitlfs.rpm

# AWS CLI
RUN \
    curl -LfSo /tmp/awscliv2.zip "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" \
    && echo "[INFO] Installing AWS CLI ..." && ( \
      unzip -q /tmp/awscliv2.zip -d /opt \
      &&  /opt/aws/install \
      &&  rm -f  /tmp/awscliv2.zip \
  ) 2>&1 1>/dev/null

# Make sure builder user exists
ARG BUILDER_UNAME=builder
ARG BUILDER_UID=1337
ARG BUILDER_GID=1337

# create group & user
RUN \
  ( \
    (getent group "${BUILDER_GID}" &> /dev/null) \
    || groupadd "${BUILDER_UNAME}" \
        --gid "${BUILDER_GID}" \
  ) && ( \
    useradd "${BUILDER_UNAME}" \
      --uid "${BUILDER_UID}" \
      --gid "${BUILDER_GID}" \
      --home-dir "/home/${BUILDER_UNAME}" \
      --create-home \
      -p "${BUILDER_UNAME}" \
  )

# Entrypoint with all SCL's/ENV enabled
COPY ./dev_tools/docker/builder/entrypoint.sh /usr/bin/entrypoint
RUN chmod a+rx "/usr/bin/entrypoint"

# Thou shall not root
USER "${BUILDER_UID}:${BUILDER_GID}"

# Setup Skeleton for RPM Builds
ENV HOME="/home/${BUILDER_UNAME}"
ENV RPM_TOPDIR="${HOME}/rpmbuild"
RUN mkdir -p "${RPM_TOPDIR}"/{BUILD,RPMS,SOURCES,SPECS,SRPMS}
RUN echo '%_topdir %{getenv:RPM_TOPDIR}/rpmbuild' > "${RPM_TOPDIR}/.rpmmacros"

ENV \
    BASH_ENV="/usr/bin/entrypoint" \
    ENV="/usr/bin/entrypoint" \
    PROMPT_COMMAND=". /usr/bin/entrypoint" \
    SCL_PYTHON_VERSION="$SCL_PYTHON_VERSION"

WORKDIR "${HOME}"

ENTRYPOINT [ "/usr/bin/entrypoint" ]