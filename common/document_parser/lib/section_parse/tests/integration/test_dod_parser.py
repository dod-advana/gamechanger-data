from unittest import TestCase, main
from itertools import chain
from os.path import dirname, abspath, join, isdir, isfile
from os import makedirs
from json import load, dump
from shutil import rmtree
import sys
sys.path.append(
    dirname(abspath(__file__)).replace("/section_parse/tests/integration", ""),
)
from section_parse.parsers import DoDParser

    

class DoDParserIntegratedTest(TestCase):
    """Integrated tests for DoDParser class."""
    DATA_DIR = dirname(abspath(__file__)).replace("integration", "data")
    EXPECTED_OUTPUT_DIR = join(DATA_DIR, "expected_outputs")
    ACTUAL_OUTPUT_DIR = join(DATA_DIR, "actual_outputs")

    @classmethod
    def setUpClass(cls) -> None:
        if isdir(cls.ACTUAL_OUTPUT_DIR):
            rmtree(cls.ACTUAL_OUTPUT_DIR)
            makedirs(cls.ACTUAL_OUTPUT_DIR, exist_ok=True)
        cls.test_full_docs = {
            "DoDD 1350.2 CH 2": {"doc_num":"1350.2"},                  
            "DoDI 8320.03 CH 3": {"doc_num":"8320.03"},
            "DoDI 8910.01 CH 1": {"doc_num":"8910.01"}
        }
        cls.test_specific_sections_docs = {
            "DoDM 6025.18": {"doc_num":"6025.18"},
            "DoDM 5120.20 CH 1": {"doc_num": "5120.20"},
            "DoDD 5105.02": {"doc_num":"5105.02"},
        }   
        for filename, doc_dict in cls.test_full_docs.items():
            doc_dict["doc_type"] = filename.split(" ")[0]
            doc_dict["expected_output"] = cls._load_expected_output(filename)
        for filename, doc_dict in cls.test_specific_sections_docs.items():
            doc_dict["doc_type"] = filename.split(" ")[0]
            doc_dict["expected_output"] = cls._load_expected_output(filename)

    def test_parse_all_sections(self):
        """Test that full documents are parsed correctly."""
        for filename, doc_dict in self.test_full_docs.items():
            fail_msg = f"Failed test case in `test_parse_all_sections()`: {filename}. "

            parser = DoDParser(doc_dict, test_mode = True)
            parser._docx_path = join(self.DATA_DIR, f"{filename}.docx")
            parser._parse()

            actual_output = [" ".join(" ".join(s).split()) for s in parser.all_sections]
            expected_output = doc_dict["expected_output"]                                      
            
            same_len = len(actual_output) == len(expected_output)
            if not same_len:
                self._save_actual_output(actual_output, filename)
                self.fail(
                    f"{fail_msg}"
                    f"\nExpected output length: {len(expected_output)}. "
                    f"\nActual output length: {len(actual_output)}."
                )

            incorrect_indices = [
                i 
                for i in range(len(expected_output)) 
                if expected_output[i] != actual_output[i]
            ]
            
            if incorrect_indices:
                self._save_actual_output(actual_output, filename)
                self.fail(
                    f"{fail_msg} Text content not the same at indices: {incorrect_indices}."
                )

    def test_specific_sections(self):
        """Verifies that specific sections are the same in the expected and 
        actual outputs."""
        for filename, doc_dict in self.test_specific_sections_docs.items():
            parser = DoDParser(doc_dict, test_mode = True)
            parser._docx_path = join(self.DATA_DIR, f"{filename}.docx")
            parser._parse()
            expected_output = doc_dict["expected_output"]  
            fields = [
                "purpose",
                "responsibilities",
                "references",
                "subject",
                "table_of_contents",
                "authorities",
                "applicability",
                "organizations",
                "summary_of_change",
                "definitions",
                "policy",
                "procedures",
            ]
            incorrect_fields = {}
            for field in fields:
                actual_output = getattr(parser, field)
                expected_output = doc_dict["expected_output"][field]
                if actual_output != expected_output:
                    incorrect_fields[field] = {
                        "actual_output": actual_output,
                        "expected_output": expected_output,
                    }
            if incorrect_fields:
                self._save_actual_output(incorrect_fields, filename)
                self.fail(
                    f"{filename}: Specific sections not as expected: {incorrect_fields.keys()}"
                )

    @classmethod
    def _load_expected_output(cls, filename):
        expected_output_path = join(cls.EXPECTED_OUTPUT_DIR, f"{filename}.json")
        if not isfile(expected_output_path):
            print(
                f"Result file does not exist at {expected_output_path}. Cannot run test_parse()."
            )
            sys.exit(1)

        with open(expected_output_path) as f:
            expected_output = load(f)

        return expected_output

    def _save_actual_output(self, actual_output, filename):
        actual_output_path = join(self.ACTUAL_OUTPUT_DIR, f"{filename}.json")
        print("Saving actual output to:", actual_output_path)
        with open(actual_output_path, "w") as f:
            dump(actual_output, f)


if __name__ == "__main__":
    main(failfast=True)
