# -*- coding: utf-8 -*-
"""
gc_crawler.validators
-----------------
Utils for validating input/output data schema.
"""

from . import INPUT_SPEC_PATH, OUTPUT_SPEC_PATH
from jsonschema import Draft7Validator as JsonSchemaValidator
from typing import Union
import json


class SchemaValidator:
    """Class for validating python dict or json object schema
    :param validator:
    """

    validator: JsonSchemaValidator

    def __init__(self, validator: JsonSchemaValidator):
        self.validator = validator

    def validate_dict(self, _dict: dict) -> None:
        self.validator.validate(_dict)

    def validate_json(self, _json: str) -> None:
        self.validate_dict(json.loads(_json))

    def validate(self, _object: Union[str, dict]) -> None:
        if isinstance(_object, str):
            self.validate_json(_object)
        elif isinstance(_object, dict):
            self.validate_dict(_object)
        else:
            raise TypeError("Tried to validate incompatible object type.")


class NoopSchemaValidator(SchemaValidator):
    """Validator that'll match any dictionary object"""

    def __init__(self):
        schema_dict = dict()
        self.validator = JsonSchemaValidator(schema=schema_dict)


class DefaultInputSchemaValidator(SchemaValidator):
    """Validator that only matches according to input_spec.json"""

    def __init__(self):
        schema_dict = json.load(open(INPUT_SPEC_PATH))
        self.validator = JsonSchemaValidator(schema=schema_dict)


class DefaultOutputSchemaValidator(SchemaValidator):
    """Validator that only matches according to output_spec.json"""

    def __init__(self):
        schema_dict = json.load(open(OUTPUT_SPEC_PATH))
        self.validator = JsonSchemaValidator(schema=schema_dict)
