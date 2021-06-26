import typing as t
import unittest as ut
from textwrap import dedent
import os

PACKAGE_PATH: str = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(PACKAGE_PATH, 'data')


def get_packages_to_import() -> t.List[str]:
    with open(os.path.join(DATA_PATH, 'package_import_list.txt'), "r") as f:
        return [l.strip() for l in f.read().split("\n") if l.strip()]


class TestImports(ut.TestCase):
    for module_name in get_packages_to_import():
        exec(dedent(f"""\
            def test_import_{module_name}(self):
                import {module_name}
                self.assertIsNotNone({module_name})
        """))