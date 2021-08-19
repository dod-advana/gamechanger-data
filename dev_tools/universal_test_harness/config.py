import os
from configuration.utils import get_connection_helper_from_env
from . import PACKAGE_PATH
from dev_tools import REPO_PATH


class Config:
    ch = get_connection_helper_from_env()
    DATA_PATH: str = os.path.join(PACKAGE_PATH, "data")
    CRAWLER_OUTPUT_PATH: str = os.path.join(DATA_PATH, "crawler_output")
    PARSED_OUTPUT_PATH: str = os.path.join(DATA_PATH, "parsed_output")
    DEFAULT_LOCAL_TEST_PATH: str = os.path.join(REPO_PATH, 'tmp', 'universal_test_harness')