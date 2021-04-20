import os

# this module's path
PACKAGE_PATH: str = os.path.dirname(os.path.abspath(__file__))
ADHOC_SQL_DIR: str = os.path.join(PACKAGE_PATH, 'adhoc')