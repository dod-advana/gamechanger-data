import unittest
import random
import sys
import os
from common.document_parser.lib.responsibility_parse import ResponsibilityParser
import pandas as pd
sys.path.append(os.path.dirname(__file__).replace("/tests/unit", ""))


class TestResponsibilityParser(unittest.TestCase):

    @classmethod
    def setUp(self) -> None:
        self.responsibility_parser = ResponsibilityParser()
        self.input_dir = os.path.join(os.path.dirname(__file__).replace("/unit", ""), "data", "input")
        self.output_dir = os.path.join(os.path.dirname(__file__).replace("/unit", ""), "data", "output")

    @classmethod
    def tearDown(self) -> None:
        for file in os.listdir(self.output_dir):
            os.remove(os.path.join(self.output_dir, file))

    def test_extract_numbering(self):
        numbering_input_output_dict = {
            "end. of a sentence and beginning of next": ("", "end. of a sentence and beginning of next"),
            "Here is some text": ("", "Here is some text"),
            "1. Here is some text": ("1.", "Here is some text"),
            "1. Here is some text": ("1.", "Here is some text"),
            "1. Here is some text": ("1.", "Here is some text"),
            "11. Here is some text": ("11.", "Here is some text"),
            "1.1. Here is some text": ("1.1.", "Here is some text"),
            "1.11. Here is some text": ("1.11.", "Here is some text"),
            "1.1.1. Here is some text": ("1.1.1.", "Here is some text"),
            "1.1.1.1. Here is some text": ("1.1.1.1.", "Here is some text"),
            "(1) Here is some text": ("(1)", "Here is some text"),
            "(11) Here is some text": ("(11)", "Here is some text"),
            "a. Here is some text": ("a.", "Here is some text"),
            "zz. Here is some text": ("zz.", "Here is some text"),
            "(a). Here is some text": ("(a).", "Here is some text"),
            "(zz). Here is some text": ("(zz).", "Here is some text"),
        }
        for input, expected_output in numbering_input_output_dict.items():
            self.assertEqual(self.responsibility_parser.extract_numbering(input), expected_output, msg=f"Error: test_extract_numbering failed on input: {input}")

    def test_parse_entities(self):
        entities_input_output_dict = {
            "Here is a sentence with no entities": [],
            "Here is a sentence with USD(P), and DoD entities": ["DoD", "USD(P)"],
            "Here is a sentence with DoD multiple times": ["DoD"]
        }
        for input, expected_output in entities_input_output_dict.items():
            actual_output = self.responsibility_parser.parse_entities(input)
            actual_output.sort()
            self.assertListEqual(actual_output, expected_output,msg=f"Error: test_parse_entities failed on input: {input}")

    def test_format_responsibility_results(self):
        file_name = "test_file.pdf"
        title = "test title"
        resp_results_input_output_dict = {
            ## TEST 1: Responsibility text that has the role and all of the responsibilties in a single block of text
            "Test Single Responsibility Line": {
                "input": [
                    "2.4 The Director, DIA, in accordance with the USD(P), shall do responsibility X. They are also "
                    "responsible for performing responsibility Y and Z."
                ],
                "output": [
                    {
                        "filename": file_name,
                        "documentTitle": title,
                        "organizationPersonnelNumbering": "2.4",
                        "organizationPersonnelText": "The Director, DIA, in accordance with the USD(P), shall do "
                                                     "responsibility X. They are also responsible for performing "
                                                     "responsibility Y and Z.",
                        "organizationPersonnelEntities": "Director, DIA;USD(P)",
                        "responsibilityNumbering": "",
                        "responsibilityText": "",
                        "responsibilityEntities": ""
                    }
                ]
            },
            ## TEST 2: Responsible role is separate from the remainder of the text sections
            "Test Multiple Responsibility Lines": {
                "input": [
                    "1. The Director, DIA shall:",
                    "1.1. Perform X responsibility",
                    "1.2. Perform Y responsibility with the Director, DLA."
                ],
                "output": [
                    {
                        "filename": file_name,
                        "documentTitle": title,
                        "organizationPersonnelNumbering": "1.",
                        "organizationPersonnelText": "The Director, DIA shall:",
                        "organizationPersonnelEntities": "Director, DIA",
                        "responsibilityNumbering": "1.1.",
                        "responsibilityText": "Perform X responsibility",
                        "responsibilityEntities": ""
                    },
                    {
                        "filename": file_name,
                        "documentTitle": title,
                        "organizationPersonnelNumbering": "1.",
                        "organizationPersonnelText": "The Director, DIA shall:",
                        "organizationPersonnelEntities": "Director, DIA",
                        "responsibilityNumbering": "1.2.",
                        "responsibilityText": "Perform Y responsibility with the Director, DLA.",
                        "responsibilityEntities": "Director, DLA"
                    }
                ]
            }
        }
        for test_description, input_output_dict in resp_results_input_output_dict.items():
            actual_output = self.responsibility_parser.format_responsibility_results(input_output_dict['input'],
                                                                                     file_name, title)
            self.assertListEqual(actual_output, input_output_dict['output'],msg=f"Error: test_format_responsibility_results failed on test case: {test_description}")

    def test_split_text_with_role_midline(self):
        input_output_dict = {
            "Work with the Director, DIA to perform responsibility X": (
                "Work with the Director, DIA to perform responsibility X", ""
            ),
            "Work with the Director, DIA in accordance with Reference (b) to perform responsibility X": (
                "Work with the Director, DIA in accordance with Reference (b) to perform responsibility X", ""
            ),
            "The Director, DIA shall: perform responsibility X and Y": (
                "The Director, DIA shall: perform responsibility X and Y", ""
            ),
            "The Director, DIA shall: (a) perform responsibility X": (
                "The Director, DIA shall:", " (a) perform responsibility X"
            ),
            "1. The Director, DIA:1.1 Work with X to perform responsibility Y": (
                "1. The Director, DIA:", "1.1 Work with X to perform responsibility Y"
            ),
        }
        for input, expected_output in input_output_dict.items():
            actual_output = self.responsibility_parser.split_text_with_role_midline(input)
            self.assertTupleEqual(actual_output, expected_output,msg=f"Error: test_split_text_with_role_midline failed on input: {input}")

    def test_parse_responsibility_lines_dodi_5000_94(self):
        with open(os.path.join(self.input_dir,"DoDI 5000.94_resp_section.txt"), "r") as file:
            resp_section_text = "".join(file.readlines())
        with open(os.path.join(self.input_dir,"DoDI 5000.94_resp_section_expected.txt"), "r") as file:
            expected_output = eval("".join(file.readlines()))

        actual_output = self.responsibility_parser.parse_responsibility_section(resp_section_text)
        self.assertListEqual(actual_output,expected_output)

    def test_extract_responsibilities_from_json_dodi_5000_94(self):
        actual_output = self.responsibility_parser.extract_responsibilities_from_json(json_filepath=
                                                                                      os.path.join(self.input_dir,"DoDI 5000.94.json"))
        with open(os.path.join(self.input_dir,"DoDI 5000.94_expected.txt"), "r") as file:
            expected_output = eval("".join(file.readlines()))

        self.assertListEqual(actual_output,expected_output)

    def test_extract_responsibilities_from_json_dodi_5000_94(self):
        actual_output = self.responsibility_parser.extract_responsibilities_from_json(json_filepath=
                                                                                      os.path.join(self.input_dir,"DoDI 5000.94.json"))
        with open(os.path.join(self.input_dir,"DoDI 5000.94_expected.txt"), "r") as file:
            expected_output = eval("".join(file.readlines()))

        self.assertListEqual(actual_output,expected_output)

    def test_extract_responsibilities_from_json_dodi_5000_94(self):
        actual_output = self.responsibility_parser.extract_responsibilities_from_json(json_filepath=
                                                                                      os.path.join(self.input_dir,"DoDI 5000.94.json"))
        with open(os.path.join(self.input_dir,"DoDI 5000.94_expected.txt"), "r") as file:
            expected_output = eval("".join(file.readlines()))

        self.assertListEqual(actual_output,expected_output)

    def test_main(self):
        actual_output_filepath = os.path.join(self.output_dir, "actual_responsibility_results.xlsx")
        expected_output = pd.read_excel(os.path.join(self.input_dir,"expected_responsibility_results.xlsx"))

        self.responsibility_parser.main(self.input_dir,
                                        excel_save_filepath=actual_output_filepath)

        # the blank file should throw an error
        self.assertSetEqual(self.responsibility_parser.error_files, {"blank_file.json"})
        # the "file_missing_responsibilties.json" should be logged as a file that doesn't contain any responsibilities
        self.assertSetEqual(self.responsibility_parser.files_missing_responsibility_section,{"file_missing_responsibilities.json"})
        # Verify out file was created
        self.assertTrue(os.path.isfile(actual_output_filepath))
        actual_output = pd.read_excel(actual_output_filepath)
        pd.testing.assert_frame_equal(expected_output,actual_output)




if __name__ == "__main__":
    main()
