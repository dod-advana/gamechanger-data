from os.path import dirname, join, basename, isfile, abspath, isdir
from os import makedirs
from shutil import rmtree
from json import load, dump
import sys

sys.path.append(
    dirname(abspath(__file__)).replace("/section_parse/tests/integration", ""),
)
from section_parse import DocxParser


DATA_DIR = dirname(abspath(__file__)).replace("integration", "data")
EXPECTED_OUTPUT_DIR = join(DATA_DIR, "expected_outputs")
ACTUAL_OUTPUT_DIR = join(DATA_DIR, "actual_outputs")


def test_parse_all_sections(docx_path, pagebreak_text):
    filename = basename(docx_path).replace(".docx", "")
    expected_output = _load_expected_output(filename)

    parser = DocxParser(docx_path)
    sections = parser.parse(pagebreak_text).sections
    sections = [" ".join(" ".join(s).split()) for s in sections]

    same_num_of_sections = _verify_number_of_sections(
        expected_output, sections, filename
    )
    if same_num_of_sections:
        same_section_texts = _verify_section_texts(
            expected_output, sections, filename
        )
        if same_section_texts:
            return True
        else:
            _save_actual_output(sections, filename)
            return False
    else:
        _save_actual_output(sections, filename)
        return False


def test_parse_specific_sections(docx_path, pagebreak_text):
    filename = basename(docx_path).replace(".docx", "")
    expected_output = _load_expected_output(filename)

    parser = DocxParser(docx_path)
    parser.parse(pagebreak_text).sections

    results = {}
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
    for field in fields:
        results[field] = _check_section(parser, expected_output, field)

    passed = all(results.values())
    if not passed:
        _save_actual_output(results, filename)

    assert (
        passed
    ), f"FAILURE: `{filename}`. The following sections do not appear as expected: {[k for k, v in results.items() if not v]}"

    return passed


def _check_section(parser, expected_outputs, field):
    sections = parser.sections
    section = getattr(sections, field)
    return section == expected_outputs[field]


def _save_actual_output(actual_output, filename):
    actual_output_path = join(ACTUAL_OUTPUT_DIR, f"{filename}.json")
    print("Saving actual output to:", actual_output_path)
    with open(actual_output_path, "w") as f:
        dump(actual_output, f)


def _verify_section_texts(expected_output, actual_output, filename):
    """Verify that the expected output and actual output have the same text in
    each section."""
    incorrect_indices = [
        i
        for i in range(len(expected_output))
        if expected_output[i] != actual_output[i]
    ]
    passed = len(incorrect_indices) == 0
    if not passed:
        _save_actual_output(actual_output, filename)
    assert (
        passed
    ), f"`FAILURE: {filename}` Section texts are not as expected for the following indices: {incorrect_indices}."

    return passed


def _verify_number_of_sections(expected_output, actual_output, filename):
    """Verify that the expected output and actual output have the same number
    of sections."""
    passed = len(expected_output) == len(actual_output)
    if not passed:
        _save_actual_output(actual_output, filename)
    assert (
        passed
    ), f"FAILURE: `{filename}`. Expected {len(expected_output)} sections but there were {len(actual_output)}"
    return len(expected_output) == len(actual_output)


def _load_expected_output(filename):
    expected_output_path = join(EXPECTED_OUTPUT_DIR, f"{filename}.json")
    if not isfile(expected_output_path):
        print(
            f"Result file does not exist at {expected_output_path}. Cannot run test_parse()."
        )
        sys.exit(1)

    with open(expected_output_path) as f:
        expected_output = load(f)

    return expected_output


if __name__ == "__main__":
    if isdir(ACTUAL_OUTPUT_DIR):
        rmtree(ACTUAL_OUTPUT_DIR)
    makedirs(ACTUAL_OUTPUT_DIR, exist_ok=True)

    results = [
        test_parse_all_sections(
            join(DATA_DIR, "DoDD 1350.2 CH 2.docx"), "DoDD 1350.2"
        ),
        test_parse_all_sections(
            join(DATA_DIR, "DoDI 8320.03 CH 3.docx"), "DoDI 8320.03"
        ),
        test_parse_all_sections(
            join(DATA_DIR, "DoDI 8910.01 CH 1.docx"), "DoDI 8910.01"
        ),
        test_parse_specific_sections(
            join(DATA_DIR, "DoDM 6025.18.docx"), "DoDM 6025.18"
        ),
        test_parse_specific_sections(
            join(DATA_DIR, "DoDM 5120.20 CH 1.docx"), "DoDM 5120.20"
        ),
    ]

    print(f"FINISHED {len(results)} PARSE TESTS.")
    print("Number of successes:", len([res for res in results if res]))
    print(f"Number of failures:", len([res for res in results if not res]))
