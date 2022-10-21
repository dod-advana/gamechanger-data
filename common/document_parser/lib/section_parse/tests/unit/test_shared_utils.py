from unittest import TestCase, main
from typing import Callable, List, Tuple, Union
from os.path import dirname
from re import Match
import sys

sys.path.append(dirname(__file__).replace("/section_parse/tests/unit", ""))
from section_parse import next_letter
from section_parse.tests import TestItem


class SharedUtilsTest(TestCase):
    """Unit tests for shared_utils.py."""

    def _run(self, func: Callable, test_cases: List[TestItem]):
        for test in test_cases:
            test.set_func(func)
            test.set_test_obj(self)
            test.verify_output()

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


if __name__ == "__main__":
    main(failfast=True)
