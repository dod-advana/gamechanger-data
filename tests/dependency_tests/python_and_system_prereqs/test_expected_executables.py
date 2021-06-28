import typing as t
import unittest as ut
from textwrap import dedent
import os
import shutil

PACKAGE_PATH: str = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(PACKAGE_PATH, 'data')


def get_executables_to_expect() -> t.List[str]:
    with open(os.path.join(DATA_PATH, 'path_executable_list.txt'), "r") as f:
        return [l.strip() for l in f.read().split("\n") if l.strip() and not l.strip().startswith("#")]


class TestExecutablesExpectedInPath(ut.TestCase):
    for executable_name in get_executables_to_expect():
        exec(dedent(f"""\
            def test_exists_in_path_{executable_name}(self):
                self.assertIsNotNone(shutil.which('{executable_name}'))
        """))