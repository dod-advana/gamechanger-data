from .config import Config
import yaml
from itertools import chain


def check_unique_service_names() -> None:
    "Make sure all service names in primary and supplementary compose files aren't duplicates"
    service_names_and_paths = []
    for path in chain([Config.MAIN_COMPOSE_FILE_PATH], Config.COMPOSE_SUPPLEMENTS.values()):
        with open(path, 'r') as f:
            d = yaml.load(f, yaml.CLoader)
            for name in d['services'].keys():
                if not name in [n for n, p in service_names_and_paths]:
                    service_names_and_paths.append((name,path))
                else:
                    dup_paths = [p for n, p in service_names_and_paths if n == name] + [path]
                    raise RuntimeError(f"Found duplicate service name {name} in compose-files {dup_paths!s}")


def check_env_file_exists() -> None:
    """Check if the .env file exists at expected location"""
    if not Config.ENV_FILE_PATH.is_file():
        raise RuntimeError(f"Could not find appropriate env_file at {Config.ENV_FILE_PATH}"
                           + "\nMake sure you run `configuration init` first")