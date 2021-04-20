from typing import Union, Any, Dict
from configuration.providers import DefaultConfigProvider
from configuration.enums import ConfigurationType
from configuration.helpers import ConnectionHelper
from configuration.renderers import ConfigRenderer, DefaultConfigRenderer
import os
from pathlib import Path
import json
from . import RENDERED_DIR
import functools


def get_config(conf_type: Union[ConfigurationType, str],
               conf_name: str,
               validate: bool = True) -> Dict[str, Any]:
    """Get config with the default provider

    :param conf_type: Name of the config type, e.g. "app-config"
    :param conf_name: Name of configuration (e.g. 'local', 'dev', corresponds to {name}.json)
    :param validate: Toggle off to avoid validating against the config jsonschema

    :return: config dictionary
    """
    return DefaultConfigProvider().get_config(conf_type, conf_name, validate)


def get_default_app_config() -> Dict[str, Any]:
    defaults_file = Path(RENDERED_DIR, "defaults.json")
    if defaults_file.exists():
        with defaults_file.open("r") as f:
            conf = json.load(f)
    else:
        conf = {}

    if os.environ.get("GC_APP_CONFIG_NAME") is not None:
        app_conf_name =  os.environ.get("GC_APP_CONFIG_NAME")
    else:
        app_conf_name = conf.get('GC_APP_CONFIG_NAME', "local")

    # app_conf_name = conf.get('GC_APP_CONFIG_NAME', "local") or os.environ.get("GC_APP_CONFIG_NAME")
    return get_config("app-config", app_conf_name)


def get_default_es_config() -> Dict[str, Any]:
    defaults_file = Path(RENDERED_DIR, "defaults.json")

    if defaults_file.exists():
        with defaults_file.open("r") as f:
            conf = json.load(f)
    else:
        conf = {}

    if os.environ.get("GC_APP_CONFIG_NAME") is not None:
        es_conf_name = os.environ.get("GC_ELASTICSEARCH_CONFIG_NAME")
    else:
        es_conf_name = conf.get('GC_ELASTICSEARCH_CONFIG_NAME', "local")

    # es_conf_name =  conf.get('GC_ELASTICSEARCH_CONFIG_NAME', "local") or os.environ.get("GC_ELASTICSEARCH_CONFIG_NAME")
    return get_config("elasticsearch-config", es_conf_name)


# TODO: deprecated, use get_default_app_config instead
def get_app_config_from_env() -> Dict[str, Any]:
    return get_default_app_config()


# TODO: deprecated, use get_default_es_config instead
def get_es_config_from_env() -> Dict[str, Any]:
    return get_default_es_config()


# TODO: deprecated, use get_default_connection_helper instead
@functools.lru_cache(maxsize=None)
def get_connection_helper_from_env() -> ConnectionHelper:
    ext_app_config_name = os.environ.get("GC_APP_CONFIG_EXT_NAME")
    if ext_app_config_name is None:
        return ConnectionHelper(get_app_config_from_env())
    else:
        with open(ext_app_config_name) as json_file:
            data = json.load(json_file)
            return ConnectionHelper(data)


def get_default_app_config_renderer() -> ConfigRenderer:
    return DefaultConfigRenderer(get_default_app_config())


def get_config_renderer_from_env() -> ConfigRenderer:
    bindings = {
        'defaults': {
          'GC_APP_CONFIG_NAME': os.environ.get("GC_APP_CONFIG_NAME", "local"),
          'GC_ELASTICSEARCH_CONFIG_NAME': os.environ.get("GC_ELASTICSEARCH_CONFIG_NAME", "local")
        },
        'docker_app_config': get_config('app-config', 'docker'),
        'app_config': get_app_config_from_env(),
        'elasticsearch_config': get_es_config_from_env()
    }
    return DefaultConfigRenderer(bindings)