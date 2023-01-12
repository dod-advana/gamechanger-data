from unittest import TestCase, main
from typing import Callable, List
import sys
from os.path import dirname
sys.path.append(dirname(__file__).replace("/section_parse/tests/unit", ""))
from section_parse import (
    find_pagebreak_date,
    match_alpha_dot,
    match_alpha_single_paren,
    match_alpha_double_parens,
    match_alpha_list_item,
    is_sentence_continuation,
    is_toc,
    is_known_section_start,
    match_enclosure_num,
    match_section_num,
)
from section_parse.tests import TestItem


class DoDUtilsTest(TestCase):
    """Unit tests for dod_utils.py."""

    def _run(self, func: Callable, test_cases: List[TestItem]):
        for test in test_cases:
            test.set_func(func)
            test.set_test_obj(self)
            test.verify_output()

    def test_find_pagebreak_date(self):
        """Verifies find_pagebreak_date()."""
        test_cases = [
            TestItem(
                (
                    "DoDD 4124.01E December 12, 1994 ENCLOSURE 1 RESPONSIBILITIES",
                ),
                (14, 31),
            )
        ]
        self._run(find_pagebreak_date, test_cases)

    def test_match_alpha_list_item(self):
        """Verifies match_alpha_list_item()."""
        test_cases = [
            TestItem(("a. Establishes policy",), ("a", match_alpha_dot)),
            TestItem(
                ("(b)  Incorporates and cancels",),
                ("b", match_alpha_double_parens),
            ),
            TestItem(
                ("c)  Provides guidance",), ("c", match_alpha_single_paren)
            ),
            TestItem(("A. REFERENCES",), (None, None)),
        ]
        self._run(match_alpha_list_item, test_cases)

    def test_is_sentence_continuation(self):
        """Verifies is_sentence_continuation()."""
        test_cases = [
            TestItem(
                (
                    "INTENSITY CONFLICT",
                    "ASSISTANT SECRETARY OF DEFENSE FOR SPECIAL OPERATIONS AND LOW-",
                ),
                True,
            ),
            TestItem(("subject to", "Serve as an approval authority, "), True),
            TestItem(
                (
                    "to execute DSCA plans as directed",
                    "Ensure the appropriate personnel are trained ",
                ),
                True,
            ),
            TestItem(("a.  Establish ", "Departments shall: "), True),
            TestItem(
                (
                    "U.S. Strategy and Policy in the War on Terror.",
                    " March 6, 2006",
                ),
                False,
            ),
            TestItem(("Section 4. ", "In accordance with "), True),
            TestItem(("Section 12 ", "As stated in "), True),
            TestItem(("Section 8 of Title 10. ", "The policy is under "), True),
            TestItem(("Section 3,", "With provision to "), True),
            TestItem(("Glossary,", "As stated in the "), True),
            TestItem(("SECTION 4. ", "In accordance with section 1."), False),
            TestItem(("GLOSSARY.", "as stated."), False),
        ]
        self._run(is_sentence_continuation, test_cases)

    def test_is_toc(self):
        """Verifies is_toc()."""
        test_cases = [
            TestItem(("TABLE OF CONTENTS",), True),
            TestItem(
                (
                    "SECTION 1:  GENERAL ISSUANCE INFORMATION .............................................................................. 3",
                ),
                True,
            ),
            TestItem(
                ("TABLE OF CONTENTS ', 'ENCLOSURE 1:  REFERENCES",), True
            ),
            TestItem(("SECTION 1.",), False),
        ]
        self._run(is_toc, test_cases)

    def test_is_known_section_start(self):
        """Verifies is_known_section_start()."""
        titles = [
            "Ref",
            "References",
            "Sub",
            "Subj",
            "Subject",
            "Applicability",
            "Policy",
            "Responsibilities",
            "Relationships",
            "Purpose",
            "Authorities",
            "Releasability",
            "Summary of Change",
            "Enclosure 1",
            "Reissuance",
            "Procedures",
            "Table of Contents",
        ]
        test_cases = [TestItem((title + ":",), True) for title in titles]
        test_cases += [TestItem((title + ".",), True) for title in titles]
        test_cases += [TestItem((title.upper(),), True) for title in titles]
        test_cases += [TestItem((title,), False) for title in titles]
        test_cases += [
            TestItem(("Glossary",), True),
            TestItem(("GLOSSARY",), True),
            TestItem(("gLOSSARY",), False),
            TestItem(("Enclosures",), True),
            TestItem(("ENCLOSURES",), True),
            TestItem(("enclosures",), False),
        ]
        self._run(is_known_section_start, test_cases)

    def test_match_enclosure_num(self):
        """Verifies match_enclosure_num()."""
        test_cases = [
            TestItem(("ENCLOSURE 1:  REFERENCES ",), "1"),
            TestItem(("ENCLOSURE 1:  REFERENCES ", "2"), None),
            TestItem(("Enclosure 1",), "1"),
            TestItem(("E.2 Responsibilities",), "2"),
            TestItem(("E3.",), "3"),
            TestItem(("E.4.1",), "4"),
            TestItem(("E.4.1", "1"), None),
            TestItem(("e5. ",), None),
            TestItem(("e5. ", "5"), None),
        ]
        self._run(match_enclosure_num, test_cases)

    def test_match_section_num(self):
        """Verifies match_section_num()."""
        test_cases = [
            TestItem(("Section 12 Purpose",), "12"),
            TestItem(("Section 12 Purpose", "2"), None),
            TestItem(("1.2.4",), "1"),
            TestItem(("1.2.4", "2"), None),
            TestItem(
                (
                    "SECTION 1:  GENERAL ISSUANCE INFORMATION .............................................................................. 3",
                    "",
                ),
                None,
            ),
            TestItem(
                (
                    "SECTION 1:  GENERAL ISSUANCE INFORMATION .............................................................................. 3",
                    "1",
                ),
                None,
            ),
        ]
        self._run(match_section_num, test_cases)


if __name__ == "__main__":
    main(failfast=True)
