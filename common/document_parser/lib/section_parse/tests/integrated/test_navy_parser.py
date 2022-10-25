from unittest import TestCase, main
from os.path import dirname, abspath, join, isdir
from os import makedirs
from shutil import rmtree
from typing import Tuple
import sys
sys.path.append(
    dirname(__file__).replace("/section_parse/tests/integrated", "")
)
from section_parse import NavyParser
from section_parse.tests import ParserTestItem


class NavyParserTest(TestCase):
    DATA_DIR = dirname(abspath(__file__)).replace("integrated", "data")
    INPUT_DIR = join(DATA_DIR, "input")
    EXPECTED_OUTPUT_DIR = join(DATA_DIR, "expected_output")
    ACTUAL_OUTPUT_DIR = join(DATA_DIR, "actual_output")

    @classmethod
    def setUpClass(cls) -> None:
        if isdir(cls.ACTUAL_OUTPUT_DIR):
            rmtree(cls.ACTUAL_OUTPUT_DIR)
        makedirs(cls.ACTUAL_OUTPUT_DIR)

    def _setup_tester_and_parser(
        self, filename: str
    ) -> Tuple[ParserTestItem, NavyParser]:
        tester = ParserTestItem(self, filename)
        tester.set_actual_output_path(self.ACTUAL_OUTPUT_DIR)
        tester.load_input(self.INPUT_DIR)
        tester.load_expected_output(self.EXPECTED_OUTPUT_DIR)

        parser = NavyParser(tester.input)

        return tester, parser

    def _verify_attribute(self, attr_name, filename):
        tester, parser = self._setup_tester_and_parser(filename)
        value = getattr(parser, attr_name)
        tester.verify_num_of_sections(value)
        tester.verify_sections_content(value)

    def test_purpose(self):
        """Verifies the purpose attribute."""
        self._verify_attribute("purpose", "navy_test_purpose.json")
        self._verify_attribute(
            "purpose", "navy_test_purpose_within_situation.json"
        )

    def test_responsibilities(self):
        """Verifies the responsibilities attribute."""
        self._verify_attribute(
            "responsibilities", "navy_test_responsibilities.json"
        )
        self._verify_attribute(
            "responsibilities", "navy_test_responsibilities_multi.json"
        )


if __name__ == "__main__":
    main(failfast=True)
