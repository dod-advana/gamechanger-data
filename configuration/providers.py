import json
from abc import ABC, abstractmethod
import typing as t
from pathlib import Path
from configuration import PACKAGE_PATH
from configuration.validators import DefaultConfigValidator
from configuration.enums import ConfigurationType


class ConfigProvider(ABC):
    """Provides config dictionaries"""

    @abstractmethod
    def get_config(self,
            conf_type: t.Union[ConfigurationType, str],
            conf_name: str,
            validate: bool = True) -> t.Dict[str, t.Any]:
        """Get config and validate it against appropriate schema

        :param conf_type: Name of the config type, e.g. "app-config"
        :param conf_name: Name of configuration (e.g. 'local', 'dev', corresponds to {name}.json)
        :param validate: Toggle off to avoid validating against the config jsonschema

        :return: config dictionary
        """
        pass


class LocalConfigProvider(ConfigProvider):

    @staticmethod
    def get_config_base_path(conf_type: ConfigurationType) -> Path:
        expected_subdir = ConfigurationType(conf_type).value
        expected_path = Path(PACKAGE_PATH, expected_subdir)

        if not expected_path.is_dir():
            raise ValueError(
                f"Expected conf base dir for conf_type '{conf_type.value}' " +
                f"does not exist: {expected_path}"
            )
        return expected_path.resolve()

    def get_available_configs(self, conf_dir: t.Union[str, Path]) -> t.Dict[str, Path]:
        conf_dir_path = Path(conf_dir).resolve()
        return { file.stem: file for file in conf_dir_path.glob("*.json") }

    def validate_config(self, conf_type: ConfigurationType, conf_dict: t.Dict[str, t.Any]) -> None:
        DefaultConfigValidator(conf_type).validate(conf_dict)  # type: ignore

    def get_config(
            self,
            conf_type: t.Union[ConfigurationType, str],
            conf_name: str,
            validate: bool = True) -> t.Dict[str, t.Any]:
        conf_type = ConfigurationType(conf_type)

        available_configs = self.get_available_configs(
            self.get_config_base_path(ConfigurationType(conf_type))
        )
        with available_configs[conf_name].open("r") as fd:
            conf_dict = json.load(fd)

        if validate:
            self.validate_config(conf_type=conf_type, conf_dict=conf_dict)
        return conf_dict


DefaultConfigProvider: ConfigProvider = LocalConfigProvider  # type: ignore