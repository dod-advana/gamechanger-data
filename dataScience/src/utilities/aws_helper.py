import boto3
import os
from dataScience.configs.config import S3Config
import logging
region = os.getenv("AWS_DEFAULT_REGION")
access_key = os.getenv("AWS_ACCESS_KEY")
secret_key = os.getenv("AWS_SECRET_KEY")
bucket_name = os.getenv("AWS_BUCKET_NAME")
env = os.getenv("ENV_TYPE")
logger = logging.getLogger("gamechanger")


def s3_connect(accessKey=access_key, secretKey=secret_key, bucketName=bucket_name):
    if bucketName is None:
        logger.warning(
            "AWS S3 env might not be set up, did you run '. dataScience/setup_env.sh'?"  # noq
        )
    if env == "prod":
        conn = boto3.Session()
    else:
        conn = boto3.Session(
            aws_access_key_id=access_key, aws_secret_access_key=secret_key
        )
    s3 = conn.resource("s3")
    bucket = s3.Bucket(bucket_name)
    return bucket


def upload_file(filepath, s3_fullpath):
    """upload_file - uploads files to s3 bucket
    Args:
        filepath: path to file
        s3_fullpath: exact path you want to save it

    Returns:
    """
    bucket = s3_connect()
    try:
        bucket.upload_file(filepath, s3_fullpath)
    except Exception as e:
        logger.debug(f"could not upload {filepath} to {s3_fullpath}")
        logger.debug(e)


def print_content(s3_path):
    """print_path - prints content of s3 path
    Args:
        s3_path: full path of s3 bucket
    Returns:
    """
    bucket = s3_connect()
    try:
        for obj in bucket.objects.filter(Prefix=s3_path):
            print(obj.key)
    except Exception as e:
        logger.debug(f"could not print path for {s3_path}")
        logger.debug(e)
