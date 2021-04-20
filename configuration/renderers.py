import typing as t
from abc import ABC, abstractmethod
from pathlib import Path
import jinja2


class ConfigRenderer(ABC):
    """Renders config file templates"""

    @abstractmethod
    def __init__(self, conf: t.Dict[str, t.Any]):
        pass

    @abstractmethod
    def render_configured(self, template_file: t.Union[Path, str]) -> str:
        pass


class JinjaConfigRenderer(ConfigRenderer):
    """Renders jinja2 template"""

    def __init__(self, conf: t.Dict[str, t.Any]):
        self.conf = conf

    def render_configured(self, template_file: t.Union[Path, str]) -> str:
        with open(template_file, "r") as f:
            return jinja2.Template(f.read()).render(**self.conf)


DefaultConfigRenderer = JinjaConfigRenderer