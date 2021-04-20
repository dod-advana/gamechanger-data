import typing as t
from configuration.providers import DefaultConfigProvider
from configuration.enums import ConfigurationType, ConfigurationEnvVar
from configuration.helpers import ConnectionHelper
from configuration.renderers import ConfigRenderer, DefaultConfigRenderer
from configuration.defaults import DEFAULT_APP_CONFIG_NAME, DEFAULT_ES_CONFIG_NAME, RENDERED_DEFAULTS_PATH
import os
from pathlib import Path
import json
from configuration import PACKAGE_PATH


def get_config(conf_type: t.Union[ConfigurationType, str],
               conf_name: str,
               validate: bool = True) -> t.Dict[str, t.Any]:
    """Get config with the default provider

    :param conf_type: Name of the config type, e.g. "app-config"
    :param conf_name: Name of configuration (e.g. 'local', 'dev', corresponds to {name}.json)
    :param validate: Toggle off to avoid validating against the config jsonschema

    :return: config dictionary
    """
    return DefaultConfigProvider().get_config(conf_type, conf_name, validate)  # type: ignore


def get_es_stopwords(stopwords_path: str = os.path.join(PACKAGE_PATH, 'elasticsearch-config/smart_stopwords.txt')) -> t.List[str]:
    """Opens custom stopwords text file as a list that can be added to the ES index"""
    return [line.strip() for line in open(stopwords_path, "r").read().split("\n") if line.strip()]


def get_rendered_defaults() -> t.Dict[str, t.Any]:
    """Get dict of default values that are rendered in the <repo>/configuration/rendered/defaults.json"""
    if RENDERED_DEFAULTS_PATH.exists():
        with RENDERED_DEFAULTS_PATH.open("r") as f:
            return json.load(f)
    else:
        return {}


# TODO: refactor to just handle different URI schemes with a single argument,
#  e.g. `file:///absolute/path/to/path/to/file` for ext config and `just_a_config_name` for named config
def get_app_config(
        explicit_app_config_name: t.Optional[str] = None,
        explicit_ext_app_config_path: t.Optional[t.Union[str, Path]] = None) -> t.Dict[str, t.Any]:
    """Get default app config.
        Precedence:
            Explicit EXT/APP Passed Path/Name (can't specify both) <-
                APP_EXT_CONFIG ENV VAR Path <- APP_EXT_CONFIG RENDERED DEFAULTS Path <-
                    APP_CONFIG ENV VAR Name <- APP_CONFIG RENDERED DEFAULTS Name <-
                        Hardcoded APP_CONFIG Default Name"""
    if explicit_app_config_name and explicit_ext_app_config_path:
        raise ValueError(f"Cannot specify both types of app config explicitly, choose one (ext) or regular")

    defaults_json = get_rendered_defaults()

    def _get_app_ext_conf(config_path: t.Optional[t.Union[str, Path]] = None) -> t.Dict[str, t.Any]:
        config_path_from_env_var = os.environ.get(ConfigurationEnvVar.APP_EXT_CONFIG_NAME.value, None)
        config_name_from_defaults_json = defaults_json.get(ConfigurationEnvVar.APP_EXT_CONFIG_NAME.value, None)
        config_path_str = config_path or config_path_from_env_var or config_name_from_defaults_json
        config_path = Path(config_path_str).resolve() if config_path_str else None

        if config_path:
            with config_path.open("r") as f:
                return json.load(f)
        else:
            return {}

    def _get_app_conf(config_name: t.Optional[str] = None) -> t.Dict[str, t.Any]:
        config_name_from_env_var = os.environ.get(ConfigurationEnvVar.APP_CONFIG_NAME.value, None)
        config_name_from_defaults_json = defaults_json.get(ConfigurationEnvVar.APP_CONFIG_NAME.value, None)
        config_name = config_name or config_name_from_env_var or config_name_from_defaults_json or DEFAULT_APP_CONFIG_NAME
        if config_name:
            return get_config(ConfigurationType.APP_CONFIG, config_name)
        else:
            return {}

    if explicit_ext_app_config_path:
        return _get_app_ext_conf(explicit_ext_app_config_path)
    if explicit_app_config_name:
        return _get_app_conf(explicit_app_config_name)

    final_conf = _get_app_ext_conf() or _get_app_conf()
    if final_conf:
        return final_conf
    else:
        # this should not ever be possible
        raise RuntimeError(f"Encountered unreachable code branch while trying to resolve app config.")


def get_es_config(explicit_es_config_name: t.Optional[str] = None) -> t.Dict[str, t.Any]:
    """Get default app config.
        Precedence: Explicit Passed Name <- ENV VAR Name <- RENDERED DEFAULTS Name <- Hardcoded Default Name"""
    defaults_json = get_rendered_defaults()

    def _get_es_config(conf_name: t.Optional[str] = None) -> t.Dict[str, t.Any]:
        conf_name_from_env_var = os.environ.get(ConfigurationEnvVar.ES_CONFIG_NAME.value, None)
        conf_name_from_defaults_json = defaults_json.get(ConfigurationEnvVar.ES_CONFIG_NAME.value, None)
        conf_name = conf_name or conf_name_from_env_var or conf_name_from_defaults_json or DEFAULT_ES_CONFIG_NAME
        if conf_name:
            return get_config(ConfigurationType.ELASTICSEARCH_CONFIG, conf_name)
        else:
            return {}

    # TODO: move this logic to the appropriate ES Index/Mapping/Settings JINJA2 templates
    #   ... may require making those templates quite bit more verbose than they currently are
    def _inject_extra_es_config(conf: t.Dict[str, t.Any]) -> t.Dict[str, t.Any]:
        try:
            conf["index"]["settings"]["analysis"]["filter"]["gc_stop"]["stopwords"] = get_es_stopwords()
        except (KeyError, TypeError):
            pass
        return conf

    final_conf = _inject_extra_es_config(_get_es_config(explicit_es_config_name))
    if final_conf:
        return final_conf
    else:
        # this should not ever be possible
        raise RuntimeError(f"Encountered unreachable code branch while trying to resolve es config.")


def get_connection_helper_from_env() -> ConnectionHelper:
    return ConnectionHelper(get_app_config())


def get_default_app_config_renderer(*args, **kwargs) -> ConfigRenderer:
    return DefaultConfigRenderer(get_app_config(*args, **kwargs))


def get_config_renderer_from_env(
        app_config_name: t.Optional[str] = None,
        es_config_name: t.Optional[str] = None,
        app_ext_config_path: t.Optional[t.Union[str, Path]] = None) -> ConfigRenderer:
    bindings = {
        'ext_configs': {
            "defaults": {
              'GC_APP_CONFIG_NAME': app_config_name,
              'GC_ELASTICSEARCH_CONFIG_NAME': es_config_name,
              'GC_APP_CONFIG_EXT_NAME': str(app_ext_config_path) if app_ext_config_path else None
            },
            "docker": get_config(ConfigurationType.APP_CONFIG, 'docker')
        },
        'app_config': get_app_config(explicit_app_config_name=app_config_name, explicit_ext_app_config_path=app_ext_config_path),
        'elasticsearch_config': get_es_config(explicit_es_config_name=es_config_name)
    }
    return DefaultConfigRenderer(bindings)