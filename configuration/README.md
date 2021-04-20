# App Configuration & More

Herein are app various drop-in app configuration files.

To add new config, simply create new json file in the right subdirectory
that conforms to correct "*.jsonschema.json" schema.

## Usage

Key features of configuration module include:
- ability to specify and retrieve app configuration in one place
- automatic enforcement of configuration schemas
- helper and utility functions for accessing accessing connection endpoints and retrieving configuration values
- extensible configuration providers and template renderers
- ability to render arbitrary text files with jinja2 templates using appropriate config context


### Getting Started

After significant changes and as a first thing after checking out a branch, it is a good idea to run `python -m configuration init -f`.
- This will copy files and render templates from `configuration/templates/` directory tree into corresponding location within
`configuration/rendered/` directory tree.

#### More about templated configs/files

For example:

If there is a `config.ini` file used in a part of the application, it can be provided as a rendered file in `configuration/templates/`
directory tree with filename like `config.ini.template`. The application can the point to `configuraiton/rendered/config.ini` as
the location of the rendered template file and the file can be rendered with appropriate configuration bindings using `configuration init`
command.

Within the template file itself, jinja2 syntax is used (<https://github.com/pallets/jinja>) and templated file suffix must be `.template`.
For example, `config.ini.template` could have a line like `ML_API_HOST={{ app_config.ml_api.host }}` and after rendering the file will be
`config.ini` and the corresponding line in it will be `ML_API_HOST=localhost`. What configuration value gets rendered here depends on the
configuration environment that was used for initialization (i.e. `configuration init --app-env <env_name> --es-env <env_name>`).

To elaborate... if `configuration init --app-config local --elasticsearch-config local` was invoked, then `configuration/app-config/local.json`
provides bindings for everything under `app_config` template variable, e.g. `{{ app_config.web_db.host }}`. And the same pattern applies to es,
with `configuration/elasticsearch-config/local.json` providing those bindings and making them available inside templates under `elasticsearch_config`
variable.

#### Retrieving configuration values

To load configuration of particular type, use the included `parsers.py` module:
```python
# for example
from configuration.utils import get_app_config, get_config

conf_type = 'app-config'
conf_name = 'dev'

config_dictionary = get_config(conf_type, conf_name)

# if you're experimenting with config and jsonschema validation breaks your flow...
validated = False
unvalidated_config_dictionary = get_config(conf_type, conf_name, validated)

# to get appropriate config for app according to env_vars/defaults
ez_config = get_app_config()
```

#### Using connection helpers

Connection helpers greatly simplify the process of connecting to common application components, like
databases, s3, es, api's, etc.
```python
# for example
from configuration.utils import get_connection_helper_from_env

ch = get_connection_helper_from_env()

ch.s3_client.list_buckets()
# {'ResponseMetadata': {'RequestId': '163D2729147F6935',
#  'HostId': '',
#  'HTTPStatusCode': 200,
# ...

ch.es_client.info()
# {'name': '8503b012b9b3',
# 'cluster_name': 'docker-cluster',
# 'cluster_uuid': '9NUNlXT7SYeEo43GKEZEEQ',
# 'version': {'number': '7.4.2',
#  'build_flavor': 'default',
#  ...

# you can also access the corresponding app config dictionary
ml_api_host = ch.conf['ml_api']['host']
```

## Extending

Drop-in configs are fully supported, but must conform to a naming schema
- brand new config types must be registered in appropriate enum `enums.ConfigurationType`
- new config of type `app-config` must reside in subdirectory called `app-config`
- new config file name should be `<name>.json`
- config contents must conform to jsonschema specified in `config-json-schemas/<conf_type>.jsonschema.json`
    - all config types must have a jsonschema file


## TODO
- secret substitution via Jinja2 template rendering
    - abstract SecretsProvider
        - local-file-based
        - S3-based
        - http-based
        - long-term
            - k8s-based (i.e. etcd)
            - many-sources (draw from first one that works)
    - renderer baked into ConfigParser
- add neo4j to config
- add mlflow to the config
- caching of parsed/validated/rendered configs (if even necessary)
- transition rest of the repo configs/secrets to here
- remove secrets non-local urls completely from the entire repo