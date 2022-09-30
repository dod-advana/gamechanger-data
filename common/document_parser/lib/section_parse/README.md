# Section Parsing

Parse documents into sections.

## Directory Structure

```
gamechanger-data/common/document_parser/lib/section_parse/

├── __init__.py
├── add_sections.py                Add document sections to a doc dict. Used in the policy analytics pipeline
├── parsers
│   ├── __init__.py
│   ├── parser_factory.py          ParserFactory class. Determines the parser to create for a given document
│   ├── parser_definition.py       ParserDefinition class. The base class for all *_parser.py files in this module
│   ├── dod_parser
│   │   ├── __init__.py
│   │   ├── dod_parser.py          DoDParser class
│   │   └── utils
│   │       ├── __init__.py
│   │       ├── section_types.py
│   │       └── utils.py
│   └── navy_parser.py             NavyParser class
├── utils
│   ├── __init__.py
│   ├── docx_parser.py             DocxParser class. Parse a docx file into paragraphs
│   └── utils.py                   Miscellaneous, shared utilities
├── tests
│   ├── __init__.py
│   ├── test_item.py
│   ├── data/*
│   ├── unit                       Unit tests
│   │   ├── __init__.py
│   │   ├── test_docx_parser.py
│   │   ├── test_utils.py
│   │   └── test_dod_parser.py
│   ├── integration                Integrated tests
│   │   ├── __init__.py
│   │   ├── test_dod_parser.py
│   │   ├── test_navy_parser.py
```

## Example Usage

### `add_sections()`

The main function of this module. Used in the Policy Analytics pipeline.

```python
from section_parse import add_sections

doc_dict = {
   "doc_type": "DoDD",
   "doc_num": "1801.04",
   "pdf_path": "./data/DoDD 1801.04.pdf",
   "text": "hello hi"
}
add_sections(doc_dict)

print("All sections:", doc_dict["sections"]["all_sections"])
print("References sections:", doc_dict["sections"]["references_section"])
print("Responsibilities sections:", doc_dict["sections"]["responsibilities_section"])
print("Purpose sections:", doc_dict["sections"]["purpose_section"])

# See add_sections for all new keys added to doc_dict.
```

### `ParserFactory`

Returns the correct parser to use for a document.

```python
from section_parse import ParserFactory

# Example 1
doc_dict = {
   "doc_type": "DoDD",
   "doc_num": "1801.04",
   "pdf_path": "./data/DoDD 1801.04.pdf", # pdf_path needed for DoD docs.
   "text": "hello hi"
}
parser = ParserFactory.create(doc_dict)  # Returns a DoDParser object for doc_dict.

# Example 2
doc_dict = {
   "doc_type": "OPNAVINST",
   "doc_num": "1253.1",
   "text": "document text"
}
parser = ParserFactory.create(doc_dict)  # Returns a NavyParser object for doc_dict.
```

## How to Run Tests

### Unit Tests

Use the unit tests to verify that individual, independent units work as expected.

1. `cd` into the [`unit`](tests/unit/) directory.
2. Run:
   ```
   python -m unittest <test module>
   ```
   where _\<test module>_ is the name of the test file to run, without the _.py_ extension.

### Integration Tests

Use the integration tests to verify that multiple units work together as expected.

1. `cd` into the [`integration`](tests/integration/) directory.
2. Run:

   ```
   python <test file name>
   ```

   where _\<test file name>_ is the name of the test file you want to run.

   - The number of successes and failures will print to the terminal.
   - For any failures, the results will be saved [here](tests/data/actual_outputs/).
