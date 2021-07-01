#!/usr/bin/env bash
set -o errexit
set -o nounset

##         ##
## CAUTION ## THIS SCRIPT IS SUPPOSED TO ONLY RUN ONCE
##         ##

TRANSFORMERS_CACHE_S3_URL="s3://data-tools-s3-2/transformer_models_v3/transformer_cache.zip"
aws s3 cp "$TRANSFORMERS_CACHE_S3_URL" /tmp/cache.zip
unzip /tmp/cache.zip -d /
rm -f /tmp/cache.zip

echo 'export TRANSFORMERS_CACHE=/transformer_cache/.cache/torch/transformers/' >> /home/gamechanger/.bashrc
chown -R gamechanger:gamechanger /home/gamechanger

python3 -m venv /opt/gc-transformer-venv
/opt/gc-transformer-venv/bin/pip install --upgrade pip setuptools wheel
/opt/gc-transformer-venv/bin/pip install -r "/home/gamechanger/gamechanger/dev/requirements/prod-transformer-venv-green.txt"
