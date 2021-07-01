from .config import Config
import subprocess as sub
from itertools import chain
import yaml
import typing as t
from functools import lru_cache


def run_or_die(*args, **kwargs):
    """Runs cmd through subprocess.run with some sane defaults"""
    return sub.run(*args, **kwargs, **dict(check=True, cwd=Config.DEV_PATH))


@lru_cache(maxsize=None)
def get_command_names() -> t.List[str]:
    """Get names of all command-type pseudo services"""
    with open(Config.COMMAND_COMPOSE_FILE_PATH, "r") as f:
        d = yaml.load(f, yaml.CLoader)
        return list(d['services'].keys())


@lru_cache(maxsize=None)
def get_main_service_names() -> t.List[str]:
    """Get names of all main services"""
    with open(Config.MAIN_COMPOSE_FILE_PATH, "r") as f:
        d = yaml.load(f, yaml.CLoader)
        return list(d['services'].keys())
