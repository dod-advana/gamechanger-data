from configuration.utils import get_connection_helper_from_env, get_config
from common.utils.s3 import S3Utils


class Conf:
    ch = get_connection_helper_from_env()
    s3_utils = S3Utils(ch)
