from unittest import TestCase, main
from typing import Callable, List
from os.path import dirname
import sys
sys.path.append(dirname(__file__).replace("/section_parse/tests/unit", ""))
from re import search
from section_parse import CJCSParser
from section_parse.tests import TestItem



class CJCSTest(TestCase):
    """Unit tests for CJCSParser.py."""

    def _run(self, func: Callable, test_cases: List[TestItem]):
        for test in test_cases:
            test.set_func(func)
            test.set_test_obj(self)
            test.verify_output()

    def _get_match_text(self, pattern, text):
        match_ = search(pattern, text)
        return match_.group() if match_ else None

    def test_enclosure_responsibilities_start_pattern(self):
        """Verifies ENCLOSURE_RESPONSIBILITIES_START_PATTERN."""

        test_case = TestItem(
            (
                CJCSParser.ENCLOSURE_RESPONSIBILITIES_START_PATTERN,
                " \n Checklist” \nF—Joint Staff Form 170, “Joint Staff Telework Employee Eligibility  \n Checklist” \nG—Emergencies \nH—Requirements \nI—Cost-Benefit Analysis of Teleworking Outside the Locality Pay Area of  \n the Traditional Worksite \nJ—References \nGL—Glossary \n \n \nUNCLASSIFIED \nCJCSI 1035.01B \n12 February 2021 \n \n4 \nUNCLASSIFIED \n \n \n \n \n \n \n \n \n \n \n \n \n \n \n \n \n \n \n \n \n \n \n(INTENTIONALLY BLANK) \n \n \n \nUNCLASSIFIED \nCJCSI 1035.01B \n12 February 2021 \n \n \nA-1 \nEnclosure A \nUNCLASSIFIED \nENCLOSURE A \n \nRESPONSIBILITIES \n \n1.",
            ),
            "ENCLOSURE A \n \nRESPONSIBILITIES",
        )
        self._run(
            self._get_match_text,
            [test_case],
        )

    def test_numbered_responsibilities_start_pattern(self):
        """Verifies NUMBERED_RESPONSIBILITIES_START_PATTERN."""
        pattern = CJCSParser.NUMBERED_RESPONSIBILITIES_START_PATTERN
        test_cases = [
            TestItem(
                (
                    pattern,
                    "See Glossary. \n \n6.  Responsibilities.  See Enclosure A. \n \n7.  Summary of Changes"
                ),
                "\n \n6.  Responsibilities"
            ),
            TestItem(
                (
                    pattern,
                    "This instruction prescribes policies, assigns responsibilities, and \noutlines procedures for participation "
                ),
                None
            ),
            TestItem(
                (
                    pattern,
                    "ENCLOSURE A \n \nRESPONSIBILITIES \n \n1.  RESPONSIBILITIES \n \n \na.  Chairman of the Joi"
                ),
                "\n \n1.  RESPONSIBILITIES"
            )
        ]
        self._run(self._get_match_text, test_cases)

    def test_numbered_purpose_start_pattern(self):
        """Verifies NUMBERED_PURPOSE_START_PATTERN."""
        pattern = CJCSParser.NUMBERED_PURPOSE_START_PATTERN
        test_cases = [
            TestItem(
                (
                    pattern,
                    " \n \n \n \nCHAIRMAN OF THE JOINT \nCHIEFS OF STAFF \nINSTRUCTION \nJ-1 \nCJCSI 1035.01A \nDISTRIBUTION:  A, B, C \n14 December 2018 \n \nJOINT STAFF TELEWORK PROGRAM \n \nReferences:  Enclosure B \n \n1.  Purpose.  This instruction prescribes policies, assigns responsibilities, and \noutlines procedures for participation in the Joint Staff (JS) Telework Program. \n \n2.  Superseded/Cancellation.  CJCSI 1035.01, “Joint Staff Telework Program,” \n22 April 2015, is hereby superseded. \n \n3.  Applicability. "
                ),
                "\n \n1.  Purpose.  "
            ),
            TestItem(
                (
                    pattern,
                    "The capabilities of FMTS are discussed in detail in the FMTS User's \nGuide, reference c. \n2.  Purpose of FMTS.  FMTS allows the Joint Staff, Combatant Commands, \nCCAs, and other joint activities to maintain, review, modify, and report \nmanpower requirements while providing a personnel database using manpower \nas the organizational structure.  "
                ),
                None
            )
        ]
        self._run(self._get_match_text, test_cases)
    
    def test_remove_pagebreaks_and_noise(self):
        """Verifies _remove_pagebreaks_and_noise()."""
        parser = CJCSParser({
            "doc_type": "CJCSI",
            "filename": "CJCSI 1001.01B.pdf",
            "text": "hi"
        })
        test_cases = [
            TestItem(
                ("\nwage grade \nCJCSI 1001.01B \n",),
                "wage grade"
            ),
            TestItem(
                ("\n(INTENTIONALLY BLANK) \n the end",),
                "the end"
            ),
            TestItem(
                ("The file was intentionally blank",),
                "The file was intentionally blank"
            ),
            TestItem(
                ("\nUNCLASSIFIED \nJOINT MANPOWER",),
                "JOINT MANPOWER"
            ),
            TestItem(
                ("The document is unclassified.\n",),
                "The document is unclassified."
            ),
            TestItem(
                ("\n \nA-1 \n REQUIREMENTS DETERMINATION",),
                "REQUIREMENTS DETERMINATION"
            ),
            TestItem(
                ("\n\nEnclosure C \nENCLOSURE C \nJOINT MANPOWER PROGRAM:",),
                "JOINT MANPOWER PROGRAM:"
            ),
            TestItem(
                ("\n7 October 2014 \n \n",),
                ""
            ),
            TestItem(
                ("civilian positions. \nCJCSI 1001.01B \n7 October 2014 \n \n \nC-4 \nEnclosure C \n \n6.  Externally Controlled Joint Manpower.",),
                "civilian positions.\n \n6.  Externally Controlled Joint Manpower."
            ),
            TestItem(
                ("U.S. Special Operations Command \nUSTRANSCOM \nUnited States Transportation Command \nVNC \nVoluntary National Contribution (NATO) \nWCF \nWorking Capital Fund \nWG \nwage grade \nCJCSI 1001.01B \n7 October 2014 \n \n \nGL-6 \nGlossary \n \n \n \n \n \n \n \n \n \n \n \n \n \n \n \n \n \n \n \n \n(INTENTIONALLY BLANK)\nCJCSI 1001.01B \n7 October 2014 \n \n \nGL-7 \nGlossary \nGLOSSARY \nPART II—DEFINITIONS",),
                "U.S. Special Operations Command \nUSTRANSCOM \nUnited States Transportation Command \nVNC \nVoluntary National Contribution (NATO) \nWCF \nWorking Capital Fund \nWG \nwage grade\nGlossary\nGlossary \nGLOSSARY \nPART II—DEFINITIONS"
            ),
        ]
        self._run(parser._remove_pagebreaks_and_noise, test_cases)
    
    def test_enclosure_title_pattern(self):
        """Verifies _make_enclosure_title_pattern()."""
        parser = CJCSParser({
            "doc_type": "CJCSI",
            "filename": "CJCSI 1001.01B.pdf",
            "text": "hi"
        })
        test_cases = [
            TestItem(
                (parser._make_enclosure_title_pattern(r"[A-Z]+"), "\nC-4 \nEnclosure C \n \n6."), 
                "\nEnclosure C \n \n"
            ),
            TestItem(
                (parser._make_enclosure_title_pattern("A"), "\nENCLOSURE A \n \nJOINT MANPOWER PROGRAM"), 
                "\nENCLOSURE A \n \n"
            ),
            TestItem(
                (parser._make_enclosure_title_pattern("C"), "\nENCLOSURE A \n \nJOINT MANPOWER PROGRAM"), 
                None
            )
        ]
        self._run(self._get_match_text, test_cases)


if __name__ == "__main__":
    main(failfast=True)
