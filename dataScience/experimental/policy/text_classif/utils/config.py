import json
import logging

logger = logging.getLogger(__name__)


class Config(object):
    def __init__(self, config_file=None):
        """
        Load configuration file; make class attributes from the key-value
        pairs (probably an easier way to do this...)

        Args:
            config_file (str): location of the configuration JSON file

        """
        # 'big' number
        self.gros = 2 ** 16 - 1.0

        self._xlate = {
            "true": True,
            "false": False,
            "gros": self.gros,
            "none": None,
        }

        with open(config_file) as f:
            cfg_dict = json.load(f)

        self._cfg = dict()
        for item, value in cfg_dict.items():
            self.__setattr__(item, self._resolve_config(value))
            logger.info(
                "{:>25s} : {}".format(item, self._resolve_config(value))
            )

    def _resolve_config(self, value):
        try:
            if value in self._xlate:
                return self._xlate[value]
            else:
                return value
        except TypeError:
            return value

    def add(self, key, value):
        self.__setattr__(key, self._resolve_config(value))
