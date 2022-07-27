from os import getenv


class S3Config:
    """Configurations for S3."""

    """S3 directory that holds ML models."""
    S3_MODELS_DIR = "models/v3/"

    """Name of the S3 Bucket to connect to."""
    BUCKET_NAME = getenv("AWS_BUCKET_NAME", default="advana-data-zone")
