from unittest import TestCase
from os.path import join
from json import load, dump
from typing import Union, List


class ParserTestItem:
    """Helper class for testing section parsers.
    See common/document_parser/lib/section_parse/tests/integrated.
    """

    def __init__(self, test_obj: TestCase, filename: str):
        """Helper class for testing section parsers.

        Args:
            test_obj (TestCase)
            filename (str): JSON file name input and expected output files.
        """
        self.test_obj = test_obj
        self.filename = filename

    def set_actual_output_path(self, dir_path: str):
        self.actual_output_path = join(dir_path, self.filename)

    def load_input(self, dir_path: str) -> None:
        """Load the object's input from a file.

        Args:
            dir_path (str): Path to the directory that contains the input file.
                Note: The filename is determined by the filename passed in
                __init__.
        """
        with open(join(dir_path, self.filename)) as f:
            file = load(f)
        self.input = file

    def load_expected_output(self, dir_path):
        """Load the object's expected output from a file.

        Args:
            dir_path (str): Path to the directory that contains the expected
                output file. Note: The expected output's filename is determined
                by the filename passed in __init__.
        """
        with open(join(dir_path, self.filename)) as f:
            file = load(f)
        self.expected_output = file

    def save_actual_output(self, actual_output) -> None:
        """Save `actual_output` as a JSON file."""
        if not hasattr(self, "actual_output_path"):
            raise AttributeError("Missing `actual_output_path`.")

        print(f"Saving actual output for `{self.filename}`.")
        with open(self.actual_output_path, "w") as f:
            dump(actual_output, f)

    def verify_num_of_sections(self, actual_output, key: Union[str, None] = None):
        """Verify that the actual output has the same number of sections as the
        object's expected output."""
        if key is None:
            expected_output = self.expected_output
        else:
            expected_output = self.expected_output[key]

        expected_len = len(expected_output)
        actual_len = len(actual_output)

        if expected_len != actual_len:
            self.save_actual_output(actual_output)

        self.test_obj.assertEqual(
            expected_len,
            actual_len,
            f"`{self.filename}`: Expected number of sections: {expected_len}. "
            f"Actual number of sections: {actual_len}.",
        )

    def verify_sections_content(self, actual_output, key: Union[str, None] = None):
        """Verify that the content of each section in the actual output is the
        same as the expected output."""
        if key is None:
            expected = self.expected_output
        else:
            expected = self.expected_output[key]

        incorrect_inds = [
            i for i in range(len(expected)) if expected[i] != actual_output[i]
        ]
        if incorrect_inds:
            self.save_actual_output(actual_output)
        msg = ""
        for i in incorrect_inds:
            msg += f"[{i}]\nExpected: `{expected[i]}`\n\nActual:   `{actual_output[i]}`\n---\n"
        self.test_obj.assertTrue(
            len(incorrect_inds) == 0,
            f"{self.filename}: Unexpected values in actual output at the "
            f"following indices: {incorrect_inds}.\n---\n{msg}",
        )
