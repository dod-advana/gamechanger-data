# Pull Tesseract 5..2.0 docker image from AWS Elastic Container Registry account: 092912502985
FROM 092912502985.dkr.ecr.us-east-1.amazonaws.com/registry1.dso.mil/ironbank/opensource/tesseract-ocr/tesseract:5.2.0 as builder

# Set container as a root user:                                                                                                                                                                       
USER root

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install RHEL tools
RUN \
    dnf -y -q update \
    &&  dnf -y -q install \
        zip \
        unzip \
        python38 \
        python38-pip \
    && dnf clean all \
    && rm -rf /var/cache/dnf

# Configure unversioned python command to python38 and create virtualenv
RUN alternatives --set python /usr/bin/python3.8 \
    && python -m venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH"

# Install parsing dependencies
COPY /dev_tools/requirements/parse-requirements.txt .

RUN pip install --upgrade pip \
    && pip install --no-deps --no-cache-dir -r parse-requirements.txt

# Install gamechangerml module
COPY var/gamechanger-ml/ .

RUN pip install --no-deps --no-cache-dir .

# Install AWS CLI
RUN pip install awscli==1.27.32

# Final build stage
FROM 092912502985.dkr.ecr.us-east-1.amazonaws.com/registry1.dso.mil/ironbank/opensource/tesseract-ocr/tesseract:5.2.0

USER root

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY --from=builder /opt/venv /opt/venv

RUN \
    dnf -y -q install \
        python38 \
        python38-pip \
    && dnf clean all \
    && rm -rf /var/cache/dnf \
    && alternatives --set python /usr/bin/python3.8

ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /gamechanger-data

COPY . .

USER 1001

ENTRYPOINT ["/bin/bash", "./ad-container-scripts/ad-reparse.sh"]

