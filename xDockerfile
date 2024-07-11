# Pull Tesseract 5..2.0 docker image from AWS Elastic Container Registry account: 092912502985
FROM 092912502985.dkr.ecr.us-east-1.amazonaws.com/registry1.dso.mil/ironbank/opensource/tesseract-ocr/tesseract:5.2.0

# Set container as a root user:
USER root

# Copy the gamechanger-data parsing requirements file
COPY /dev_tools/requirements/parse-requirements.txt .

# Install RHEL tools:
RUN dnf -y update \
    && dnf install -y glibc-locale-source.x86_64 \
    && dnf -y install \
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
        python38-devel.x86_64 \
        python38-Cython \
        openblas \
        openblas-threads \
        diffutils \
        file \
    && dnf clean all \
    && rm -rf /var/cache/yum

RUN ln -s /usr/bin/python3 /usr/bin/python & ln -s /usr/bin/pip3 /usr/bin/pip

# Install requirements
RUN pip install --upgrade pip setuptools wheel \
    && pip install -r parse-requirements.txt --no-deps

WORKDIR /gamechanger-data

ENTRYPOINT ["bash"]
