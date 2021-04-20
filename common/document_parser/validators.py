import json
import jsonschema
import traceback
from pathlib import Path
from common import PACKAGE_DOCUMENT_PARSER_PATH
import os


def verify_file(json_file:str) -> bool:
    """
    take in a Json file and compare it vs a json schema to verify it
    Args:
        json_file: location of the json file

    Returns: True if valid
    """
    schema_path = os.path.join(PACKAGE_DOCUMENT_PARSER_PATH,'output_schema.json')
    try:
        with open(schema_path, 'r') as f:
            schema_dict = json.load(f)
        with open(json_file, 'r') as f:
            input_json_dict = json.load(f)
        jsonschema.validate(input_json_dict, schema_dict)
    except jsonschema.exceptions.ValidationError as e:
        print("well formed but invalid json")
        print(e)
        is_valid_json = False
        return is_valid_json
    except json.decoder.JSONDecodeError as e:
        print("not a json")
        is_valid_json = False
        traceback.print_exec()
        return is_valid_json
    else:
        is_valid_json = True
    return is_valid_json


def verify_directory(json_directory:str)->bool:
    """
    take in a Json directory and compare them vs a json schema to verify it
    Args:
        json_directory: location of the json files

    Returns: True if valid

    """
    p = Path(json_directory).glob("*.json")
    files = [x for x in p if x.is_file()]
    is_valid = False
    for m_file in files:
        is_valid = verify_file(str(m_file))
        print("Validation OK - " + str(m_file))
        if is_valid is False:
            print("Validation Failed - " + str(m_file))
            break
    return is_valid


def verify(source:str) -> bool:
    """
    take in a Json directory and compare them vs a json schema to verify it
    Args:
        source: location of the json files

    Returns: True if valid

    """
    if Path(source).is_file():
        result = verify_file(source)
    else:
        result = verify_directory(source)
    return result
