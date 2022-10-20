import unittest
import random
import sys
import os
from common.document_parser.lib.responsibility_parse import ResponsibilityParser
sys.path.append(os.path.dirname(__file__).replace("/tests/unit", ""))


class TestResponsibilityParser(unittest.TestCase):

    @classmethod
    def setUp(self) -> None:
        self.responsibility_parser = ResponsibilityParser()
        self.input_dir = os.path.join(os.path.dirname(__file__).replace("/unit",""), "data", "input")
        self.output_dir = os.path.join(os.path.dirname(__file__).replace("/unit",""), "data", "output")

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
            self.assertEqual(self.responsibility_parser.extract_numbering(input), expected_output)

    def test_parse_entities(self):
        entities_input_output_dict = {
            "Here is a sentence with no entities": [],
            "Here is a sentence with USD(P), and DoD entities": ["DoD","USD(P)"],
            "Here is a sentence with DoD multiple times":["DoD"]
           }
        for input, expected_output in entities_input_output_dict.items():
            actual_output = self.responsibility_parser.parse_entities(input)
            actual_output.sort()
            self.assertListEqual(actual_output, expected_output)


if __name__ == "__main__":
    main(failfast=True)