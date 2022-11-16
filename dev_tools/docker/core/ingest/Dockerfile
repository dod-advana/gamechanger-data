# Initial build stage
FROM 092912502985.dkr.ecr.us-east-1.amazonaws.com/registry1.dso.mil/ironbank/opensource/python/python38 as builder

USER root

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install RHEL tools
RUN \
    dnf -y -q update \
    &&  dnf -y -q install \
        zip \
        unzip \
    && dnf clean all \
    && rm -rf /var/cache/dnf

# Create virtualenv
RUN python -m venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH"

# Install ingest dependencies
COPY /dev_tools/requirements/ingest-requirements.txt .

RUN /opt/venv/bin/python -m pip install --upgrade pip \
    && pip install --no-deps --no-cache-dir -r ingest-requirements.txt

# Install AWS CLI
RUN curl -LfSo /tmp/awscliv2.zip "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" \
    && unzip -q /tmp/awscliv2.zip -d /opt \
    && /opt/aws/install --bin-dir /aws-cli-bin \
    && rm -f /tmp/awscliv2.zip

# Install gamechangerml module
COPY var/gamechanger-ml/ .

RUN pip install --no-deps --no-cache-dir .

# Final build stage
FROM 092912502985.dkr.ecr.us-east-1.amazonaws.com/registry1.dso.mil/ironbank/opensource/python/python38

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /aws-cli-bin /usr/local/bin
COPY --from=builder /usr/local/aws-cli /usr/local/aws-cli

ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /gamechanger-data

COPY . .

USER 1001                                                                                                                                                                                                                                                     

ENTRYPOINT ["/bin/bash", "./tmp/crawl_ingest.sh"]
