from unittest import TestCase, main
from typing import Callable, List
from os.path import dirname
from re import search, RegexFlag, VERBOSE
import sys

sys.path.append(dirname(__file__).replace("/section_parse/tests/unit", ""))
from section_parse import (
    next_letter,
    DD_MONTHNAME_YYYY,
    remove_pagebreaks,
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
                (DD_MONTHNAME_YYYY, "\n7 MARCH 2016 \n", [VERBOSE]),
                "7 MARCH 2016"
            ),
            TestItem(
                (DD_MONTHNAME_YYYY, "2 January 1998", [VERBOSE]),
                "2 January 1998"
            ),
            TestItem(
                (DD_MONTHNAME_YYYY, "12 February 1", [VERBOSE]),
                None
            ), 
            TestItem(
                (DD_MONTHNAME_YYYY, "hey 17 Aug 1998 hello", [VERBOSE]),
                "17 Aug 1998"
            )
        ]
        self._run(self._get_match_text, test_cases)

    def test_remove_pagebreaks(self):
        test_cases = [
            TestItem(
                ("DoDI 1235.12, June 7, 2016 \nChange 1, 02/27/2017 \n9 \nENCLOSURE 2 ", r"[0-9]", []),
                "DoDI 1235.12, June 7, 2016 \nChange 1, 02/27/2017\nENCLOSURE 2 "
            )
        ]
        self._run(remove_pagebreaks, test_cases)


if __name__ == "__main__":
    main(failfast=True)
