import json
import logging

logger = logging.getLogger(__name__)


def read_json(json_file):
    with open(json_file) as fp:
        json_dict = json.load(fp)
    return json_dict
