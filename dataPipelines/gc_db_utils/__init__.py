import os

# this module's path
PACKAGE_PATH: str = os.path.dirname(os.path.abspath(__file__))

# init db bindings
import dataPipelines.gc_db_utils.web
import dataPipelines.gc_db_utils.orch