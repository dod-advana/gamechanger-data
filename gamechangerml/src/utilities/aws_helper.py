import boto3
import os
from gamechangerml.configs.config import S3Config
import logging

bucket_name = os.getenv("AWS_BUCKET_NAME", default="advana-data-zone")
env = os.getenv("ENV_TYPE")
logger = logging.getLogger("gamechanger")


def s3_connect():
    conn = boto3.Session()
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

def list_folders(bucket, prefix):

	client = boto3.client('s3')
	result = client.list_objects(Bucket=bucket, Prefix=prefix, Delimiter='/')
	for o in result.get('CommonPrefixes'):
		print('sub folder : ', o.get('Prefix'))
