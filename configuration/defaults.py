from . import RENDERED_DIR
from pathlib import Path

DEFAULT_APP_CONFIG_NAME = "local"
DEFAULT_ES_CONFIG_NAME = "local"
RENDERED_DEFAULTS_PATH = Path(RENDERED_DIR, "defaults.json")
TEMPLATE_FILENAME_SUFFIX = '.template'