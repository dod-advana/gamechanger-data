#!/bin/sh
set -e
mkdir -p $FILE_DIR && mlflow server \
      --backend-store-uri file://${FILE_DIR} \
      --default-artifact-root s3://${AWS_BUCKET}/artifacts \
      --host 0.0.0.0 \
      --port 5050

