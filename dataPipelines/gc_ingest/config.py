from configuration.utils import get_connection_helper_from_env
from common.utils.s3 import S3Utils
import datetime
from enum import Enum


class CheckpointedJobType(Enum):
    CRAWLER_UPLOAD = 'crawler-upload'
    MANUAL_UPLOAD = 'manual-upload'


class Config:
    TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S"

    # TODO: this should lazy load separately from the constants, else if endpoints are not availalable - things will break
    connection_helper = get_connection_helper_from_env()

    default_batch_timestamp = datetime.datetime.utcnow()
    default_batch_timestamp_str = default_batch_timestamp.strftime(TIMESTAMP_FORMAT)
    s3_bucket = connection_helper.conf['aws']['bucket_name']

    # TODO: this should lazy load separately from the constants, else if endpoints are not availalable - things will break
    s3_utils = S3Utils(connection_helper, bucket=s3_bucket)


