from unittest import TestCase, main
from typing import Callable, List
from os.path import dirname
from re import search, RegexFlag, VERBOSE, IGNORECASE
import sys

sys.path.append(dirname(__file__).replace("/section_parse/tests/unit", ""))
from section_parse import (
    next_letter,
    DD_MONTHNAME_YYYY,
)
from section_parse.tests import TestItem


class SharedUtilsTest(TestCase):
    """Unit tests for shared_utils.py."""

    def _run(self, func: Callable, test_cases: List[TestItem]):
        for test in test_cases:
            test.set_func(func)
            test.set_test_obj(self)
            test.verify_output()

    def _get_match_text(self, pattern, text, regex_flags : List[RegexFlag]=[]):
        flags = 0
        for flag in regex_flags:
            flags |= flag
        match_ = search(pattern, text, flags=flags)
        return match_.group() if match_ else None

    def test_next_letter(self):
        """Verifies next_letter()."""
        inputs_should_raise = ["abc", "3"]
        for input_ in inputs_should_raise:
            try:
                next_letter(input_)
            except ValueError:
                pass
            else:
                self.fail(f"Failed to raise ValueError for input: `{input_}`")

        letters = "abcdefghijklmnopqrstuvwxyza"
        test_cases = []
        for i, letter in enumerate(letters[:-1]):
            test_cases.append(TestItem((letter,), letters[i + 1]))

        self._run(next_letter, test_cases)

    def test_DD_MONTHNAME_YYYY(self):
        """Verifies DD_MONTHNAME_YYYY."""
        test_cases = [
            TestItem(
                (DD_MONTHNAME_YYYY, "\n7 MARCH 2016 \n", [VERBOSE, IGNORECASE]),
                "7 MARCH 2016"
            ),
            TestItem(
                (DD_MONTHNAME_YYYY, "2 January 1998", [VERBOSE, IGNORECASE]),
                "2 January 1998"
            ),
            TestItem(
                (DD_MONTHNAME_YYYY, "12 February 1", [VERBOSE, IGNORECASE]),
                None
            )
        ]
        self._run(self._get_match_text, test_cases)


if __name__ == "__main__":
    main(failfast=True)
