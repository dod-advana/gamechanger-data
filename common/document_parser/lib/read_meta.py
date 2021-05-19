import json
from pathlib import Path


def read_metadata(meta_data) -> dict:
    if not meta_data:
        return {}

    if type(meta_data) == dict:
        return meta_data

    if type(meta_data) == str:
        meta_fname = Path(meta_data)
    else:
        meta_fname = meta_data
    try:
        with open(meta_fname) as f_in:
            data = json.load(f_in)
    except:
        return {}

    return data


