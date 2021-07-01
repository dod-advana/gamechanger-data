from dev_tools import PACKAGE_PATH
from pathlib import Path
from configuration.utils import get_default_app_config_renderer
from configuration import RENDERED_DIR


class Config:
    DEV_PATH = PACKAGE_PATH
    PROJECT_DIR = DEV_PATH
    MAIN_COMPOSE_FILE_PATH = Path(DEV_PATH, 'docker-compose.yaml').resolve()
    SUPPLEMENTARY_COMPOSE_DIR = Path(DEV_PATH, 'supplementary-compose-files').resolve()
    COMPOSE_SUPPLEMENTS = {
        n: p for n, p in (
            (f.name.rsplit(".", 2)[0], str(f))
            for f in SUPPLEMENTARY_COMPOSE_DIR.glob("*.docker-compose.yaml")
        )
    }
    COMMAND_COMPOSE_FILE_PATH = COMPOSE_SUPPLEMENTS['commands']

    ENV_FILE_PATH = Path(RENDERED_DIR, 'composectl/.env')
    BASE_DOCKER_COMPOSE_ARGS = [
        'docker-compose',
        '--project-dir', str(PROJECT_DIR),
        '--env-file', str(ENV_FILE_PATH),
        '-f', str(MAIN_COMPOSE_FILE_PATH)
    ]
    renderer=get_default_app_config_renderer()