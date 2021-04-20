from enum import Enum


class ConfigurationType(Enum):
    APP_CONFIG = "app-config"
    ELASTICSEARCH_CONFIG = "elasticsearch-config"


# when changing, also check <repo>/configuration/templates/defaults.json.template
# when changing, also check <repo>/configuration/utils.py::get_config_renderer_from_env(...)
class ConfigurationEnvVar(Enum):
    # config from <repo>/configuration/app-config/<config-name>.json
    APP_CONFIG_NAME = 'GC_APP_CONFIG_NAME'
    # config from <app-config-name>.json - path to file
    APP_EXT_CONFIG_NAME = 'GC_APP_CONFIG_EXT_NAME'
    # config from <repo>/configuration/elasticsearch-config/<config-name>.json
    ES_CONFIG_NAME = 'GC_ELASTICSEARCH_CONFIG_NAME'