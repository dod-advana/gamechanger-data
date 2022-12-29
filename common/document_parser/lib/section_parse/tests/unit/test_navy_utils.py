from unittest import TestCase, main
from typing import Callable, List, Tuple, Union
from os.path import dirname
from re import Match
import sys

sys.path.append(dirname(__file__).replace("/section_parse/tests/unit", ""))
from section_parse import (
    get_letter_dot_section,
    match_number_hyphenated_section,
    match_number_dot_section,
    match_first_appendix_title,
)
from section_parse.tests import TestItem


class NavyUtilsTest(TestCase):
    """Unit tests for navy_utils.py."""

    def _run(self, func: Callable, test_cases: List[TestItem]):
        for test in test_cases:
            test.set_func(func)
            test.set_test_obj(self)
            test.verify_output()

    def _run_matches(
        self, func, test_cases: List[Tuple[TestItem, Union[str, None]]]
    ):
        # Run test cases for a function that returns a Match object.
        # Since we can't directly initialize a Match object, we can't pass the
        # expected output to a TestItem init. Therefore, we verify the function
        # output by checking the output match group.
        for test, expected_match in test_cases:
            test.set_func(func)
            test.set_test_obj(self)
            test.verify_type()

            if expected_match:
                self.assertEqual(
                    test.actual_output.group(),
                    expected_match,
                    f" Input was {test.inputs}. Expected match was "
                    f"`{expected_match}` but actual match was "
                    f"`{test.actual_output.group()}`.",
                )

    def test_get_letter_dot_section(self):
        """Verifies get_letter_dot_section()."""
        text = "\n1.  Situation \n \n    a.  Purpose.  In accordance with the references (a) through (l), this \nMarine Corps Bulletin (MCBUL) provides guidance to standardize a Marine Corps \ncapability executed from garrison that seamlessly provides uninterrupted Full \nMotion Video (FMV) Processing, Exploitation, and Dissemination (PED) support \nto MAGTF, Naval, Joint, and Coalition operations. \n \n    b.  Background.  In September 2014, the Marine Corps Director of \nIntelligence (DIRINT) published MCISRE Plan 2015-2020, reference (a), calling \nfor “Marine Corps participation in Joint PED centers and the provision for \nJoint PED from within the MCISRE, beginning with Marine Corps Intelligence \nActivity (MCIA).”  PED is a Marine Corps capability that supports the MAGTF, \nNaval, Joint Force, and Coalition partners.  This capability will be employed \nto meet mission requirements outlined by the Global Force Management process \nto include unique organic mission requirements across the MAGTF.  MCIA and \nMARSOC nodes are currently operational and train to standards outlined in \nUSSOCOM Manual 350-16 reference (b).  USSOCOM PED standards are universally \nrecognized as the Joint Force standard.  Marine Corps PED training is being \ndeveloped and implemented, and will continue to adhere to USSOCOM training \nMCBUL 3800 \n6 AUG 2020 \n \n2 \nstandards to ensure interoperability across the Joint Force.  In accordance \nwith references (c) and (d), the establishment of Marine Corps PED nodes are \ndefined at MCIA, MARSOC, I MEF (Camp Pendleton and MCAS Yuma), II MEF (Camp \nLejeune), and III MEF (Camp Hansen).  As Marine Corps PED nodes achieve \nInitial Operating Capacity (IOC), the Service must standardize and codify \nmanpower implementation and training requirements for the Marines responsible \nfor PED execution.   \n \n2.  Mission. "
        test_cases = [
            TestItem(
                (text, "purpose"),
                "\n \n    a.  Purpose.  In accordance with the references (a) through (l), this \nMarine Corps Bulletin (MCBUL) provides guidance to standardize a Marine Corps \ncapability executed from garrison that seamlessly provides uninterrupted Full \nMotion Video (FMV) Processing, Exploitation, and Dissemination (PED) support \nto MAGTF, Naval, Joint, and Coalition operations. ",
            ),
            TestItem(
                (text, "background"),
                "\n \n    b.  Background.  In September 2014, the Marine Corps Director of \nIntelligence (DIRINT) published MCISRE Plan 2015-2020, reference (a), calling \nfor “Marine Corps participation in Joint PED centers and the provision for \nJoint PED from within the MCISRE, beginning with Marine Corps Intelligence \nActivity (MCIA).”  PED is a Marine Corps capability that supports the MAGTF, \nNaval, Joint Force, and Coalition partners.  This capability will be employed \nto meet mission requirements outlined by the Global Force Management process \nto include unique organic mission requirements across the MAGTF.  MCIA and \nMARSOC nodes are currently operational and train to standards outlined in \nUSSOCOM Manual 350-16 reference (b).  USSOCOM PED standards are universally \nrecognized as the Joint Force standard.  Marine Corps PED training is being \ndeveloped and implemented, and will continue to adhere to USSOCOM training \nMCBUL 3800 \n6 AUG 2020 \n \n2 \nstandards to ensure interoperability across the Joint Force.  In accordance \nwith references (c) and (d), the establishment of Marine Corps PED nodes are \ndefined at MCIA, MARSOC, I MEF (Camp Pendleton and MCAS Yuma), II MEF (Camp \nLejeune), and III MEF (Camp Hansen).  As Marine Corps PED nodes achieve \nInitial Operating Capacity (IOC), the Service must standardize and codify \nmanpower implementation and training requirements for the Marines responsible \nfor PED execution.   ",
            ),
        ]
        self._run(get_letter_dot_section, test_cases)

    def test_match_number_hyphenated_section(self):
        """Verifies match_number_hyphenated_section()."""
        test_cases = [
            (
                TestItem(
                    (
                        "as stated.\n1-2. PURPOSE\nThis publication...",
                        "1",
                        "2",
                    ),
                    Match,
                ),
                "\n1-2.",
            ),
            (
                TestItem(
                    ("as stated.\n2-4 PURPOSE\nThis publication...", "1"), None
                ),
                None,
            ),
            (
                TestItem(
                    ("as stated.\n2-4 PURPOSE\nThis publication...", "2"),
                    Match,
                ),
                "\n2-4 ",
            ),
            (
                TestItem(
                    ("as stated.\n2-4 PURPOSE\nThis publication...", "2", "4"),
                    Match,
                ),
                "\n2-4 ",
            ),
            (
                TestItem(
                    ("as stated.\n2-4 PURPOSE\nThis publication...", "3", "4"),
                    None,
                ),
                None,
            ),
            (
                TestItem(
                    ("as stated.\n2-4 PURPOSE\nThis publication...", "2", "1"),
                    None,
                ),
                None,
            ),
            (
                TestItem(
                    ("as stated.\n2-4.\nPURPOSE\nThis publication...",), Match
                ),
                "\n2-4.",
            ),
        ]
        self._run_matches(match_number_hyphenated_section, test_cases)

    def test_match_number_dot_section(self):
        """Verifies match_number_dot_section()."""
        text = "in paragraph 6d of reference (a). \n \n2. At any time that you anticipate a change in your availability"
        test_cases = [
            (TestItem((text, "2"), Match), "\n2."),
            (TestItem((text,), Match), "\n2."),
            (TestItem((text, "3"), None), None),
            (TestItem(("NAVMC 3500.100C I",), None), None),
        ]
        self._run_matches(match_number_dot_section, test_cases)

    def test_match_first_appendix_title(self):
        """Verifies match_first_appendix_title() (and therefore also verifies
        APPENDIX_TITLE_PATTERN).
        """
        test_cases = [
            (
                TestItem(("OPNAVINST\nA-1 Appendix A \nREFERENCES",), Match),
                "\nA-1 Appendix A \n",
            ),
            (TestItem(("\nRef: \nSee appendix A \n \n1.",), None), None),
            (
                TestItem((" END.\nAppendix B \n- \nForms",), Match),
                "\nAppendix B \n",
            ),
        ]
        self._run_matches(match_first_appendix_title, test_cases)


if __name__ == "__main__":
    main(failfast=True)
