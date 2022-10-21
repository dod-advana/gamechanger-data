# Section Parsing

## Directory Structure

```
gamechanger-data/common/document_parser/lib/section_parse/

├── __init__.py
├── add_sections.py                     Add document sections to a doc dict. Used in the policy analytics pipeline
├── parsers
│   ├── __init__.py
│   ├── parser_factory.py               ParserFactory class. Determines the parser to create for a given document
│   ├── parser_definition.py            ParserDefinition class. Base class for all section parsers
│   ├── dod_parser.py                   DoDParser class
│   ├── navy_parser.py                  NavyParser class
│   └── cjcs_parser.py                  CJCSParser class
├── utils
│   ├── __init__.py
│   ├── shared_utils.py
│   ├── dod_utils.py                    Utils for DoDParser
│   └── navy_utils.py                   Utils for NavyParser
├── tests
│   ├── __init__.py
│   ├── test_item.py
│   ├── parser_test_item.py
│   ├── data                            Test data
│   │   ├── input/*.json
│   │   └── expected_output/*.json
│   ├── unit                            Unit tests
│   │   ├── __init__.py
│   │   ├── test_shared_utils.py
│   │   ├── test_dod_utils.py
│   │   ├── test_navy_utils.py
│   │   └── test_cjcs.py
│   ├── integrated                      Integrated tests
│   │   ├── __init__.py
│   │   ├── test_dod_parser.py
│   │   ├── test_navy_parser.py
│   │   └── test_cjcs_parser.py
```

## Example Usage

### [`add_sections()`](add_sections.py)

```python
doc_dict = {
    "doc_type": "DoDD",
    "filename": "DoDD 1234.05.pdf",
    "text": "document text here"
}
add_sections(doc_dict)
# Sections will be added to doc_dict under the key "sections"
```

## Tests

1. Activate your virtual environment with the project's package requirements.

2. `cd` into the directory that contains the test file you want to run

   - [`unit`](tests/unit/) for unit tests
   - [`integrated`](tests/integrated/) for integrated tests

3. Run:
   ```
   python -m unittest <test file name>
   ```
   replace _\<test file name>_ with the name of the test file to run (e.g., _test_dod_utils.py_)
