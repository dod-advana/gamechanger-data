import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


def to_config_dir():
    here = os.path.dirname(os.path.realpath(__file__))
    p = Path(here)
    config_path = os.path.join(
        here, os.path.join(p.parents[0], "configuration")
    )
    return config_path
