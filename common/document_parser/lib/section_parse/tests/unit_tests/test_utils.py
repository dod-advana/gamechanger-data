"""Tests for common.document_parser.lib.section_parse.utils.utils"""

from unittest import TestCase, main
from os.path import dirname

import sys
sys.path.append(
    dirname(__file__).replace("/section_parse/tests/unit_tests", "")
)
from section_parse.tests import verify_output, make_fail_msg
from section_parse.utils import (
    match_section_num,
    match_roman_numerals,
    match_enclosure_num,
    match_num_list_item,
    match_num_dot,
    match_num_parentheses,
    is_alpha_list_item,
    is_sentence_continuation,

)


class UtilsTest(TestCase):
    def test_match_section_num(self):

        """Verifies match_section_num()"""
        inputs_and_expected_outputs = {
            ("Section 5", None): "5",
            ("Section 5", "5"): "5",
            ("hello section 4", "12"): None,
            ("hello section 7", None): None,
            ("Section 2", "4"): None,
            ("A.2. Procedures", None): "A.2",
            ("1.14", None): "1",
            ("1.14", "2.14"): None,
        }

        for inputs, expected_output in inputs_and_expected_outputs.items():
            if len(inputs) != 2:
                self.fail(
                    make_fail_msg("match_section_num()") + "not length 2."
                )
            verify_output(
                self,
                expected_output,
                match_section_num(inputs[0], inputs[1]),
                make_fail_msg(
                    "match_section_num()",
                    f"text={inputs[0]}, num={str(inputs[1])}",
                ),
            )

    def test_match_roman_numerals(self):
        """Verifies match_roman_numerals()."""
        inputs_and_expected_outputs = {"III. ": 3, "II ": 2, "XLARGE": None}
        fail_msg = "Failure for match_roman_numerals(). Input was: "

        for input_, expected_output in inputs_and_expected_outputs.items():
            try:

                verify_output(
                    self,
                    expected_output,
                    match_roman_numerals(input_),
                    fail_msg + f"`{input_}`. ",
                )
            except Exception as e:
                print("------", e)
                raise e

    def test_match_enclosure_num(self):
        """Verifies match_enclosure_num()."""
        with self.assertRaises(ValueError):
            match_enclosure_num("", return_type="hi")
            match_enclosure_num("", return_type="string")
            match_enclosure_num("", return_type="int")
            match_enclosure_num("", return_type="list")

        inputs_and_expected_outputs = {
            ("Enclosure 4", None, "str"): "4",
            ("Enclosure 3", "4", "bool"): False,
            ("Enclosure 4", "4", "bool"): True,
            ("E1.  Enclosure 1", None, "str"): "1",
        }

        for inputs, expected_output in inputs_and_expected_outputs.items():
            if len(inputs) != 3:
                self.fail(
                    make_fail_msg("match_enclosure_num()")
                    + "Input was not length 3."
                )
            verify_output(
                self,
                expected_output,
                match_enclosure_num(inputs[0], inputs[1], inputs[2]),
                make_fail_msg(
                    "match_enclosure_num()",
                    f"text={inputs[0]}, num={inputs[1]}, return_type={inputs[2]}",
                ),
            )

    def test_match_num_list_item(self):
        """Verifies match_num_list_item()."""
        inputs_and_expected_outputs = {
            "1.": "1",
            "(2)": "2",
            "3)": "3",
            "hello 1.": None,
        }
        for input_, expected_output in inputs_and_expected_outputs.items():
            verify_output(
                self,
                expected_output,
                match_num_list_item(input_),
                make_fail_msg("match_num_list_item()", input_),
            )

    def test_match_num_dot(self):
        """Verifies match_num_dot()."""
        inputs_and_expected_outputs = {
            "12.": "12",
            "3": None,
            "hello 4.": None,
        }
        for input_, expected_output in inputs_and_expected_outputs.items():
            verify_output(
                self,
                expected_output,
                match_num_dot(input_),
                make_fail_msg("match_num_dot()", input_),
            )

    def test_match_num_parentheses(self):
        """Verifies match_num_parentheses()."""
        inputs_and_expected_outputs = {
            "(1)": "1",
            "2)": "2",
            "3": None,
            "hello (1)": None,
        }
        for input_, expected_output in inputs_and_expected_outputs.items():
            verify_output(
                self,
                expected_output,
                match_num_parentheses(input_),
                make_fail_msg("match_num_parentheses()", input_)
            )
    
    def test_is_bold(self):
        """Verifies is_bold()."""
        # TODO

    def test_is_first_line_indented(self):
        """Verifies is_first_line_indented()."""
        # TODO

    def test_is_sentence_continuation(self):
        """Verifies is_sentence_continuation()."""
        name = "is_sentence_continuation()"
        inputs_and_expected_outputs = {
            ("hello", "she says "): True,
            ("hello", "she says."): False,
            ("Hello", "she says "): False,
        }
        for inputs, expected_output in inputs_and_expected_outputs.items():
            if len(inputs) != 2:
                self.fail(make_fail_msg(name) + "Input was not length 2.")
            verify_output(
                self,
                expected_output,
                is_sentence_continuation(inputs[0], inputs[1]),
                make_fail_msg(name, inputs)
            )
        

    def test_is_alpha_list_item(self):
        """Verifies is_alpha_list_item()."""
        inputs_and_expected_outputs = {
            "a. Responsibilities": True,
            "aa. Procedures": True,
            "(a) Policy": True,
            "a Reference": False,
            "reference (a)": False,
        }
        for input_, expected_output in inputs_and_expected_outputs.items():
            verify_output(
                self,
                expected_output,
                is_alpha_list_item(input_),
                make_fail_msg("is_alpha_list_item()", input_)
            )

    # TODO here


if __name__ == "__main__":
    main(failfast=True)
