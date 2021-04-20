import json
from . import CONFIG_JSON_SCHEMA_PATH
from jsonschema import Draft7Validator as JsonSchemaValidator
from jsonschema import ValidationError
import typing as t
from pathlib import Path
from abc import ABC, abstractmethod
from configuration.enums import ConfigurationType


class ConfigurationValidator(ABC):
    """Validates config schema and correctness"""

    @abstractmethod
    def __init__(self, conf_type: ConfigurationType):
        pass

    @abstractmethod
    def validate(self, _object: t.Union[str, t.Dict[str, t.Any]]) -> None:
        pass


class LocalJSONSchemaValidator(ConfigurationValidator):
    def __init__(self, conf_type: ConfigurationType):
        self.conf_type = ConfigurationType(conf_type)

        self.schema_path = Path(
            CONFIG_JSON_SCHEMA_PATH,
            f"{self.conf_type.value}.jsonschema.json"
        )

        with self.schema_path.open("r") as f:
            self.schema_dict = json.load(f)

        self.validator = JsonSchemaValidator(self.schema_dict)

    def validate_dict(self, _dict: dict) -> None:
        errors = self.validator.iter_errors(_dict)

        failed = False
        for error in errors:
            failed = True
            print(error)
            print('------')
        if failed:
            raise ValidationError("JSONSchema validation error, see console output for info")

    def validate_json(self, _json: str) -> None:
        self.validate_dict(json.loads(_json))

    def validate(self, _object: t.Union[str, t.Dict[str, t.Any]]) -> None:
        if isinstance(_object, str):
            self.validate_json(_object)
        elif isinstance(_object, dict):
            self.validate_dict(_object)
        else:
            raise ValueError("Tried to validate incompatible object type.")


DefaultConfigValidator: ConfigurationValidator = LocalJSONSchemaValidator  # type: ignore
