FROM registry1.dso.mil/ironbank/opensource/python/python38

USER root

# Copying requirements file
COPY /ingest-requirements-min.txt .

# Install RHEL tools
RUN \
    dnf -y update \
    && dnf install -y glibc-locale-source.x86_64 \
    &&  dnf -y install \
        zip \
        unzip \
        gzip \
        zlib \
        zlib-devel \
        git \
        git-lfs \
        make \
        automake \
        autoconf \
        libtool \
        gcc \
        gcc-c++ \
        gcc-gfortran \
        libpng \
        libpng-devel \
        libtiff \
        libtiff-devel \
        libjpeg-turbo \
        libjpeg-turbo-devel \
        python38 \
        python38-devel \
        python38-Cython \
        openblas \
        openblas-threads \
        diffutils \
        file \
    && dnf clean all \
    && rm -rf /var/cache/yum

# Install requirements
RUN pip install --upgrade pip setuptools wheel \
    && pip install -r ingest-requirements-min.txt

WORKDIR /gamechanger-data

ENTRYPOINT [ "bash" ]