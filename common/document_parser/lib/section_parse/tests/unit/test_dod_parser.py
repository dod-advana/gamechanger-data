"""Unit tests for the DoDParser class."""

from unittest import TestCase, main
from os.path import dirname
from itertools import chain
import sys
sys.path.append(dirname(__file__).replace("/section_parse/tests/unit", ""))
from section_parse.parsers import DoDParser


class SectionsTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        doc_dict = {"doc_type": "DoDI", "doc_num": "472"}

        # Set up for test_combine_glossary().
        cls.glossary = DoDParser(doc_dict, test_mode=True)
        cls.glossary._sections = [
            ["GLOSSARY"],
            [
                "G.1.  ACRONYMS. ",
                "ASD(HA) CFR \nDHA \nDHS \nDoDD \nDoDI \nFDA \nFOIA \nGC DoD \nHHS \nHITECH \nHIPAA \nIRB \nMHS \nMTF \nNoPP \nPHI \nPII \nUCMJ \nU.S.C. ",
            ],
            [
                "G.2.  DEFINITIONS.  Unless otherwise noted, these terms and their definitions are for the purpose of this issuance."
            ],
            [
                "GLOSSARY",
                "The Glossary definitions assign HIPAA-specific meanings to the following common terms:",
            ],
        ]

        # Set up for test_combine_by_section_num_1().
        cls.section_nums_1 = DoDParser(doc_dict, test_mode=True)
        cls.section_nums_1._sections = [
            ["SECTION 4.USES AND DISCLOSURES OF PHI "],
            [
                "4.1.  GENERAL RULES ON USES OR DISCLOSURES OF PHI. ",
                "a.  Standard:  Permitted and Prohibited Uses and Disclosures. ",
                "4.2.  USES AND DISCLOSURES FOR WHICH AN AUTHORIZATION IS REQUIRED.",
            ],
            [
                "4.3.  USES AND DISCLOSURES REQUIRING AN OPPORTUNITY FOR INDIVIDUAL TO AGREE OR TO OBJECT."
            ],
            [
                "(a)  A public health authority or other government authority authorized by law to receive reports of child abuse or neglect. "
            ],
            ["SECTION 5.RIGHTS OF INDIVIDUALS"],
            [
                "5.1.  NOTICE OF PRIVACY PRACTICES (NOPP) FOR PHI. ",
                "a.  Standard:  NoPP. ",
            ],
        ]

        # Set up for test_combine_by_section_num_2().
        cls.section_nums_2 = DoDParser(doc_dict, test_mode=True)
        cls.section_nums_2._sections = [
            ["1.  PURPOSE.  This instruction: "],
            [
                "1.1.  Reissues DoD Directive (DoDD) 8320.03 (Reference (a)) as a DoD Instruction (DoDI) in accordance with the authority in DoDD 5135.02 (Reference (b)) to establish policy and assign responsibilities for creation, maintenance, and dissemination of UID standards to account for, control, and manage DoD assets and resources. "
            ],
            [
                "a.  Supports the National Military Strategy of the United States of America "
            ],
            [
                "2.  APPLICABILITY.  This instruction applies to OSD, the Military Departments, the Office of the Chairman of the Joint Chiefs of Staff (CJCS) and the Joint Staff, the Combatant Commands, the Office of the Inspector General of the Department of Defense, the Defense Agencies, "
            ],
            [
                "the DoD Field Activities, and all other organizational entities within the DoD (referred to collectively in this instruction as the DoD Components). "
            ],
            [" 3.  POLICY.  It is DoD policy to: "],
        ]

        # Set up for test_combine_enclosures().
        cls.enclosures = DoDParser(doc_dict, test_mode=True)
        cls.enclosures._sections = [
            ["ENCLOSURE 1 REFERENCES "],
            [
                "(a) \tDoD 5120.20-R, “Management and Operation of Armed Forces Radio and Television \tService (AFRTS),” November 1998 (hereby cancelled) \n"
            ],
            [
                "(b) \tDoD Directive 5122.05, “Assistant to the Secretary of Defense for Public Affairs \t(ATSD(PA)),” August 7, 2017 \n"
            ],
            ["ENCLOSURE 2 PROCEDURES "],
            [
                "1. AFRTS SERVICE (NEW AND/OR ALTERED)",
                "a. American Forces Network (AFN) Outlets.  Manned AFN outlets (affiliates) produce local internal information products (such as spot announcements, news, and live radio shows) and insert them into radio and TV streams received from American Forces Network-Broadcast Center (AFN-BC). ",
            ],
            ["2. USE OF PROGRAM MATERIALS"],
            ["E3.  ENCLOSURE 3 \nMEO REPORTING REQUIREMENTS "],
        ]

        # Set up for test_remove_repeated_section_titles().
        cls.repeated_titles = DoDParser(doc_dict, test_mode=True)
        cls.repeated_titles._sections = [
            [
                "SECTION 3",
                "3.1.  LEGAL AUTHORITIES IN GENERAL. ",
                "a.  General Provisions.",
                "SECTION 3",
                "(1)  Preemption of State Law. ",
            ],
            [
                "ENCLOSURE 1 REFERENCES",
                "(a) DoD Instruction 8910.01, 'Information Collection and Reporting,' March 6, 2007, as amended (hereby cancelled)",
                "(b) DoD Directive 5144.02, “DoD Chief Information Officer (DoD CIO),” April 22, 2013 (c) Chapter 35 of Title 44, United States Code ",
                "ENCLOSURE 1",
            ],
        ]

    def test_combine_glossary(self):
        """Verifies _combine_glossary()."""
        expected_output = [list(chain.from_iterable(self.glossary.all_sections))]
        self.glossary._combine_glossary()
        actual_output = self.glossary.all_sections
        self.assertEqual(
            actual_output,
            expected_output,
            self._make_fail_msg(
                "test_combine_glossary", expected_output, actual_output
            ),
        )

    def test_combine_section_nums_1(self):
        """Verifies _combine_section_nums()."""
        expected_output = [
            [
                "SECTION 4.USES AND DISCLOSURES OF PHI ",
                "4.1.  GENERAL RULES ON USES OR DISCLOSURES OF PHI. ",
                "a.  Standard:  Permitted and Prohibited Uses and Disclosures. ",
                "4.2.  USES AND DISCLOSURES FOR WHICH AN AUTHORIZATION IS REQUIRED.",
                "4.3.  USES AND DISCLOSURES REQUIRING AN OPPORTUNITY FOR INDIVIDUAL TO AGREE OR TO OBJECT.",
                "(a)  A public health authority or other government authority authorized by law to receive reports of child abuse or neglect. ",
            ],
            [
                "SECTION 5.RIGHTS OF INDIVIDUALS",
                "5.1.  NOTICE OF PRIVACY PRACTICES (NOPP) FOR PHI. ",
                "a.  Standard:  NoPP. ",
            ],
        ]
        self.section_nums_1._combine_section_nums()
        actual_output = self.section_nums_1.all_sections
        self.assertEqual(
            actual_output,
            expected_output,
            self._make_fail_msg(
                "test_combine_by_section_num_1",
                expected_output,
                actual_output,
            ),
        )

    def test_combine_section_nums_2(self):
        """Verifies _combine_section_nums()."""
        expected_output = [
            [
                "1.  PURPOSE.  This instruction: ",
                "1.1.  Reissues DoD Directive (DoDD) 8320.03 (Reference (a)) as a DoD Instruction (DoDI) in accordance with the authority in DoDD 5135.02 (Reference (b)) to establish policy and assign responsibilities for creation, maintenance, and dissemination of UID standards to account for, control, and manage DoD assets and resources. ",
                "a.  Supports the National Military Strategy of the United States of America ",
            ],
            [
                "2.  APPLICABILITY.  This instruction applies to OSD, the Military Departments, the Office of the Chairman of the Joint Chiefs of Staff (CJCS) and the Joint Staff, the Combatant Commands, the Office of the Inspector General of the Department of Defense, the Defense Agencies, ",
                "the DoD Field Activities, and all other organizational entities within the DoD (referred to collectively in this instruction as the DoD Components). ",
            ],
            [" 3.  POLICY.  It is DoD policy to: "],
        ]
        self.section_nums_2._combine_section_nums()
        actual_output = self.section_nums_2.all_sections
        self.assertEqual(
            actual_output,
            expected_output,
            self._make_fail_msg(
                "test_combine_by_section_num_2", expected_output, actual_output
            ),
        )

    def test_combine_enclosures(self):
        """Verifies _combine_enclosures()."""
        expected_output = [
            [
                "ENCLOSURE 1 REFERENCES ",
                "(a) \tDoD 5120.20-R, “Management and Operation of Armed Forces Radio and Television \tService (AFRTS),” November 1998 (hereby cancelled) \n",
                "(b) \tDoD Directive 5122.05, “Assistant to the Secretary of Defense for Public Affairs \t(ATSD(PA)),” August 7, 2017 \n",
            ],
            [
                "ENCLOSURE 2 PROCEDURES ",
                "1. AFRTS SERVICE (NEW AND/OR ALTERED)",
                "a. American Forces Network (AFN) Outlets.  Manned AFN outlets (affiliates) produce local internal information products (such as spot announcements, news, and live radio shows) and insert them into radio and TV streams received from American Forces Network-Broadcast Center (AFN-BC). ",
                "2. USE OF PROGRAM MATERIALS",
            ],
            [
                "E3.  ENCLOSURE 3 \nMEO REPORTING REQUIREMENTS ",
            ],
        ]
        self.enclosures._combine_enclosures()
        actual_output = self.enclosures.all_sections
        self.assertEqual(
            actual_output,
            expected_output,
            self._make_fail_msg(
                "test_combine_enclosures", expected_output, actual_output
            ),
        )

    def test_remove_repeated_section_titles(self):
        """Verifies _remove_repeated_section_titles()."""
        expected_output = [
            [
                "SECTION 3",
                "3.1.  LEGAL AUTHORITIES IN GENERAL. ",
                "a.  General Provisions.",
                "(1)  Preemption of State Law. ",
            ],
            [
                "ENCLOSURE 1 REFERENCES",
                "(a) DoD Instruction 8910.01, 'Information Collection and Reporting,' March 6, 2007, as amended (hereby cancelled)",
                "(b) DoD Directive 5144.02, “DoD Chief Information Officer (DoD CIO),” April 22, 2013 (c) Chapter 35 of Title 44, United States Code ",
            ],
        ]
        self.repeated_titles._remove_repeated_section_titles()
        actual_output = self.repeated_titles.all_sections
        self.assertEqual(
            actual_output,
            expected_output,
            self._make_fail_msg(
                "test_remove_repeated_section_titles",
                expected_output,
                actual_output,
            ),
        )

    def _make_fail_msg(
        self, func_name: str, expected_output, actual_output
    ) -> str:
        return (
            f"FAILURE: `{func_name}()`.\nExpected output: {expected_output}."
            f"\n\nActual output: {actual_output}",
        )


if __name__ == "__main__":
    main(failfast=True)
