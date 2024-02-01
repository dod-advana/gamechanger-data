import tempfile
import os
from pathlib import Path
from common.document_parser.cli import pdf_to_json
from common.tests import PACKAGE_OCR_PDF_PATH

import json
import pytest
import shutil
from dev_tools import REPO_PATH

ORIGINAL_TEST_FILES = dict(
        non_ocr_html_file=os.path.join(REPO_PATH,
                                   "dev_tools/universal_test_harness/data/crawler_output/dfar_data/FAR Part 1.html"),
        non_ocr_html_metadata_file=os.path.join(REPO_PATH,
                                   "dev_tools/universal_test_harness/data/crawler_output/dfar_data/FAR Part 1.html.metadata")
)

def test_single_process_non_ocr_text_file():
    # Set up test parameters
    parser_path = "common.document_parser.parsers.policy_analytics.parse::parse"
    verify = False #True
    ocr_missing_doc = True
    num_ocr_threads = 2

    # Get the directory of the script
    script_dir = Path(__file__).resolve().parent

    # Create a temporary directory for testing
    #temp_dir = tempfile.mkdtemp()

    # Set up input and output paths
    input_file = ORIGINAL_TEST_FILES['non_ocr_html_file']
    metadata_input_file = ORIGINAL_TEST_FILES['non_ocr_html_metadata_file']

    # Call the pdf_to_json function
    pdf_to_json(
        parser_path=parser_path,
        source=input_file,
        metadata=metadata_input_file,
        destination="/home/gamechanger/gamechanger-data/out",
        verify=verify,
        ocr_missing_doc=ocr_missing_doc,
        num_ocr_threads=num_ocr_threads
    )

# Run the test
test_single_process_non_ocr_text_file()