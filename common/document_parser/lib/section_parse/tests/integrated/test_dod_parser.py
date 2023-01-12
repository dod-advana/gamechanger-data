from unittest import TestCase, main
from os.path import dirname, abspath, join, isdir
from os import makedirs
from shutil import rmtree
import sys
sys.path.append(
    dirname(__file__).replace("/section_parse/tests/integrated", "")
)
from section_parse import DoDParser
from section_parse.tests import ParserTestItem


class DoDParserTest(TestCase):
    DATA_DIR = dirname(abspath(__file__)).replace("integrated", "data")
    INPUT_DIR = join(DATA_DIR, "input")
    EXPECTED_OUTPUT_DIR = join(DATA_DIR, "expected_output")
    ACTUAL_OUTPUT_DIR = join(DATA_DIR, "actual_output")

    @classmethod
    def setUpClass(cls) -> None:
        if isdir(cls.ACTUAL_OUTPUT_DIR):
            rmtree(cls.ACTUAL_OUTPUT_DIR)
        makedirs(cls.ACTUAL_OUTPUT_DIR)

    def _run_test(
        self, method_name: str, filename: str, key: str = "all_sections"
    ):
        tester = ParserTestItem(self, filename)
        tester.set_actual_output_path(self.ACTUAL_OUTPUT_DIR)
        tester.load_input(self.INPUT_DIR)
        tester.load_expected_output(self.EXPECTED_OUTPUT_DIR)

        parser = DoDParser(tester.input, True)
        parser._sections = tester.input[key]

        method = getattr(parser, method_name)
        method()

        tester.verify_num_of_sections(parser._sections, key)
        tester.verify_sections_content(parser._sections, key)

    def test_combine_toc(self):
        """Verifies _combine_toc()."""
        self._run_test("_combine_toc", "dod_test_combine_toc.json")

    def test_remove_pagebreaks_and_noise(self):
        """Verifies _remove_pagebreaks_and_noise()."""
        self._run_test(
            "_remove_pagebreaks_and_noise", "dod_test_remove_pagebreaks.json"
        )

    def test_combine_alpha_list_items(self):
        """Verifies _combine_alpha_list_items()."""
        self._run_test(
            "_combine_alpha_list_items",
            "dod_test_combine_alpha_list_items.json",
        )

    def test_combine_by_section_nums(self):
        """Verifies _combine_by_section_nums()."""
        self._run_test(
            "_combine_by_section_nums", "dod_test_combine_by_section_nums.json"
        )

    def test_combine_enclosures(self):
        """Verifies _combine_enclosures()."""
        self._run_test(
            "_combine_enclosures", "dod_test_combine_enclosures.json"
        )

    def test_combine_glossary_then_references(self):
        """Verifies _combine_glossary_then_references()."""
        self._run_test(
            "_combine_glossary_then_references",
            "dod_test_combine_glossary_then_references.json",
        )

    def test_combine_enclosures_list(self):
        """Verifies _combine_enclosures_list()."""
        self._run_test(
            "_combine_enclosures_list", "dod_test_combine_enclosures_list.json"
        )


if __name__ == "__main__":
    main(failfast=True)
