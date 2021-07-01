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
    ocr_pdf_file=os.path.join(REPO_PATH,
                              "dev_tools/universal_test_harness/data/crawler_output/2021-01-01T110000/Title 1.pdf"),
    ocr_pdf_metadata_file=os.path.join(REPO_PATH,
                                       "dev_tools/universal_test_harness/data/crawler_output/2021-01-01T110000/Title 1.pdf.metadata"),
    non_ocr_pdf_file=os.path.join(REPO_PATH,
                                  "dev_tools/universal_test_harness/data/crawler_output/2021-01-01T110000/Title 2.pdf"),
    non_ocr_pdf_metadata_file=os.path.join(REPO_PATH,
                                           "dev_tools/universal_test_harness/data/crawler_output/2021-01-01T110000/Title 2.pdf.metadata")
)

EXPECTED_OUTPUT_FILES = dict(
    ocr_json_file="Title 1.json",
    non_ocr_json_file="Title 2.json",
)


@pytest.fixture(scope='function')
def parsed_doc_output_dir(tmpdir) -> str:
    yield str(tmpdir)


@pytest.fixture(scope='function')
def input_dir_with_one_ocr_raw_doc(tmpdir) -> str:
    shutil.copy(ORIGINAL_TEST_FILES['ocr_pdf_file'], tmpdir)
    shutil.copy(ORIGINAL_TEST_FILES['ocr_pdf_metadata_file'], tmpdir)
    yield str(tmpdir)


@pytest.fixture(scope='function')
def input_dir_with_one_non_ocr_raw_doc(tmpdir) -> str:
    shutil.copy(ORIGINAL_TEST_FILES['non_ocr_pdf_file'], tmpdir)
    shutil.copy(ORIGINAL_TEST_FILES['non_ocr_pdf_metadata_file'], tmpdir)
    yield str(tmpdir)


@pytest.fixture(scope='function')
def input_dir_with_ocr_and_non_ocr_raw_doc(tmpdir) -> str:
    shutil.copy(ORIGINAL_TEST_FILES['ocr_pdf_file'], tmpdir)
    shutil.copy(ORIGINAL_TEST_FILES['ocr_pdf_metadata_file'], tmpdir)
    shutil.copy(ORIGINAL_TEST_FILES['non_ocr_pdf_file'], tmpdir)
    shutil.copy(ORIGINAL_TEST_FILES['non_ocr_pdf_metadata_file'], tmpdir)
    yield str(tmpdir)


def test_single_process_ocr_doc(input_dir_with_one_ocr_raw_doc,
                                parsed_doc_output_dir):
    parser_path = "common.document_parser.parsers.policy_analytics.parse::parse"
    verify = True
    ocr_missing_doc = True
    num_ocr_threads = 2
    pdf_to_json(
        parser_path=parser_path,
        source=ORIGINAL_TEST_FILES["ocr_pdf_file"],
        metadata=ORIGINAL_TEST_FILES["ocr_pdf_metadata_file"],
        destination=parsed_doc_output_dir,
        verify=verify,
        ocr_missing_doc=ocr_missing_doc,
        num_ocr_threads=num_ocr_threads
    )

    f_name = EXPECTED_OUTPUT_FILES["ocr_json_file"]
    json_fp = f"{parsed_doc_output_dir}/{f_name}"

    out_dict = None
    with open(json_fp) as f:
        out_dict = json.load(f)

    assert out_dict is not None


def test_single_process_non_ocr_doc(input_dir_with_one_non_ocr_raw_doc,
                                    parsed_doc_output_dir):
    parser_path = "common.document_parser.parsers.policy_analytics.parse::parse"
    verify = True
    ocr_missing_doc = True
    num_ocr_threads = 2
    pdf_to_json(
        parser_path=parser_path,
        source=ORIGINAL_TEST_FILES["non_ocr_pdf_file"],
        metadata=ORIGINAL_TEST_FILES["non_ocr_pdf_metadata_file"],
        destination=parsed_doc_output_dir,
        verify=verify,
        ocr_missing_doc=ocr_missing_doc,
        num_ocr_threads=num_ocr_threads
    )

    def _assert_parsed_dir_has_what_i_expect():

        f_name = EXPECTED_OUTPUT_FILES["non_ocr_json_file"]
        json_fp = f"{parsed_doc_output_dir}/{f_name}"

        out_dict = None
        with open(json_fp) as f:
            out_dict = json.load(f)

        return out_dict is not None

    assert _assert_parsed_dir_has_what_i_expect()


def test_single_process_non_ocr_doc_no_metadata(input_dir_with_one_non_ocr_raw_doc,
                                                parsed_doc_output_dir):
    parser_path = "common.document_parser.parsers.policy_analytics.parse::parse"
    verify = True
    ocr_missing_doc = True
    num_ocr_threads = 2
    pdf_to_json(
        parser_path=parser_path,
        source=ORIGINAL_TEST_FILES["non_ocr_pdf_file"],
        destination=parsed_doc_output_dir,
        verify=verify,
        ocr_missing_doc=ocr_missing_doc,
        num_ocr_threads=num_ocr_threads
    )

    f_name = EXPECTED_OUTPUT_FILES["non_ocr_json_file"]
    json_fp = f"{parsed_doc_output_dir}/{f_name}"

    out_dict = None
    with open(json_fp) as f:
        out_dict = json.load(f)

    assert out_dict is not None


def test_single_process_mixed_dir(input_dir_with_ocr_and_non_ocr_raw_doc,
                                  parsed_doc_output_dir):
    parser_path = "common.document_parser.parsers.policy_analytics.parse::parse"
    verify = True
    ocr_missing_doc = True
    num_ocr_threads = 2
    pdf_to_json(
        parser_path=parser_path,
        source=input_dir_with_ocr_and_non_ocr_raw_doc,
        metadata=input_dir_with_ocr_and_non_ocr_raw_doc,
        destination=parsed_doc_output_dir,
        verify=verify,
        ocr_missing_doc=ocr_missing_doc,
        num_ocr_threads=num_ocr_threads
    )

    f_name = EXPECTED_OUTPUT_FILES["non_ocr_json_file"]
    json_fp = f"{parsed_doc_output_dir}/{f_name}"
    out_dicts = []
    for f_name in [EXPECTED_OUTPUT_FILES["non_ocr_json_file"], EXPECTED_OUTPUT_FILES["ocr_json_file"]]:
        json_fp = f"{parsed_doc_output_dir}/{f_name}"
        out_dict = None
        with open(json_fp) as f:
            out_dict = json.load(f)
            out_dicts.append(out_dict)

    assert None not in out_dicts


def test_multiprocess_mixed_dir(input_dir_with_ocr_and_non_ocr_raw_doc,
                                parsed_doc_output_dir):
    parser_path = "common.document_parser.parsers.policy_analytics.parse::parse"
    verify = True
    ocr_missing_doc = True
    num_ocr_threads = 2
    pdf_to_json(
        parser_path=parser_path,
        source=input_dir_with_ocr_and_non_ocr_raw_doc,
        metadata=input_dir_with_ocr_and_non_ocr_raw_doc,
        destination=parsed_doc_output_dir,
        verify=verify,
        ocr_missing_doc=ocr_missing_doc,
        num_ocr_threads=num_ocr_threads,
        multiprocess=0
    )

    f_name = EXPECTED_OUTPUT_FILES["non_ocr_json_file"]
    json_fp = f"{parsed_doc_output_dir}/{f_name}"
    out_dicts = []
    for f_name in [EXPECTED_OUTPUT_FILES["non_ocr_json_file"], EXPECTED_OUTPUT_FILES["ocr_json_file"]]:
        json_fp = f"{parsed_doc_output_dir}/{f_name}"
        out_dict = None
        with open(json_fp) as f:
            out_dict = json.load(f)
            out_dicts.append(out_dict)

    assert None not in out_dicts
