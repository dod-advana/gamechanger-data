import json
import os

def read_extension_conf() -> dict:
    ext_app_config_name = os.environ.get("GC_APP_CONFIG_EXT_NAME")
    with open(ext_app_config_name) as json_file:
        data = json.load(json_file)
    return data
