"""Tests for common.document_parser.lib.section_parse.utils.section_types"""

from unittest import TestCase, main
from typing import Callable, List
from os.path import dirname
import sys

sys.path.append(
    dirname(__file__).replace("/section_parse/tests/unit", "")
)
from section_parse.tests import TestItem
from section_parse.utils import (
    is_enclosure_continuation,
    should_skip,
    is_known_section_start,
    is_child,
    is_same_section_num,
)


class SectionTypesTest(TestCase):
    def _run(self, func: Callable, test_cases: List[TestItem]):
        for test in test_cases:
            test.set_func(func)
            test.set_test_obj(self)
            test.verify_output()

    def test_is_enclosure_continuation(self):
        """Verifies is_enclosure_continuation."""
        test_cases = [
            TestItem(("RESPONSIBILITIES", ["ENCLOSURE 1"]), True),
            TestItem(("ABBREVIATIONS", ["GLOSSARY"]), False),
            TestItem(("1. Acronyms", ["Enclosure 2"]), False),
            TestItem(("ENCLOSURE 1 REFERENCES", ["Enclosure 1"]), True),
        ]
        self._run(is_enclosure_continuation, test_cases)

    def test_should_skip(self):
        """Verifies should_skip()."""
        test_cases = [
            TestItem(("44", ""), True),
            TestItem(("DoDI 1000.31, October 26, 2018  4", "DoDI 1000.31"), True),
            TestItem(("Change 2, 08/31/2018 	2 ", ""), True),
            TestItem(("08/31/2018\t2", ""), True),
            TestItem(("10\tENCLOSURE 5", ""), True),   
            TestItem(("ENCLOSURE 4", ""), False)            
        ]
        self._run(should_skip, test_cases)

    def test_is_known_section_start(self):
        """Verifies is_known_section_start."""
        # TODO
        # test_cases = [
        #     TestItem(("TABLE OF CONTENTS.... SECTION 1"), False),
        #     TestItem((), ),
        #     TestItem((), ),
        #     TestItem((), ),
        #     TestItem((), ),
               
        # ]
        # self._run(is_known_section_start, test_cases)

    # def test_is_child(self):
    # TODO
    #     """Verifies ."""
    #     test_cases = [
    #         TestItem((), ),

    #     ]
    #     self._run(, test_cases)

    # def test_is_same_section_num(self):
    # TODO
    #     """Verifies ."""
    #     test_cases = [
    #         TestItem((), ),

    #     ]
    #     self._run(, test_cases)

    # def test_(self):
    #     """Verifies ."""
    #     test_cases = [
    #         TestItem((), ),

    #     ]
    #     self._run(, test_cases)


if __name__ == "__main__":
    main(failfast=True)
