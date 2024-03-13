# Use Ubuntu 20.04 as the base image
FROM ubuntu:20.04


# Install Tesseract OCR and Python 3.8 along with essential build tools
RUN apt-get update && \
    apt-get install -y tesseract-ocr \
                       python3.8 \
                       python3-pip \
                       python3.8-dev \
                       python3.8-venv \
                       build-essential \
                       libpng-dev \
                       libtiff-dev \
                       libjpeg-dev \
                       libwebp-dev \
                       git \
                       git-lfs \
                       zip \
                       unzip \
                       gzip \
                       zlib1g-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Update pip, setuptools, and wheel
RUN python3.8 -m pip install --upgrade pip setuptools wheel

# Install the AWS CLI
RUN pip install awscli

# Copy files into the container
COPY . /gamechanger-data/

# Install Python dependencies
RUN pip install --no-deps -r /gamechanger-data/dev_tools/requirements/gc-venv-current.txt

# Set the working directory for the container
WORKDIR /gamechanger-data

# Set bash as the default entry point
ENTRYPOINT ["bash"]
