from configuration.utils import get_connection_helper_from_env


class Config:
    connection_helper = get_connection_helper_from_env()
