from configuration.utils import get_connection_helper_from_env
from dataPipelines.gc_db_utils.utils import check_if_table_or_view_exists
from . import REPO_PATH
import os
from functools import lru_cache

class Config:
    connection_helper = get_connection_helper_from_env()
    abbcount_json_path = os.path.join(REPO_PATH, "gamechangerml/src/featurization/data/abbcounts.json")
    agencies_csv_path = os.path.join(REPO_PATH, "gamechangerml/data/agencies/agencies.csv")

    @classmethod
    @lru_cache(maxsize=None)
    def does_assist_table_exist(cls):
        return check_if_table_or_view_exists(
            db_engine=cls.connection_helper.web_db_engine,
            table_or_view='gc_assists'
        )
