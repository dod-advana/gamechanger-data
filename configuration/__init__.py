import os

PACKAGE_PATH: str = os.path.dirname(os.path.abspath(__file__))
CONFIG_JSON_SCHEMA_PATH: str = os.path.join(PACKAGE_PATH, 'config-json-schemas')
TEMPLATE_DIR: str = os.path.join(PACKAGE_PATH, 'templates')
RENDERED_DIR: str = os.path.join(PACKAGE_PATH, 'rendered')