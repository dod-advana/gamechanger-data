# Section Parsing

This module supports parsing DoD documents into sections. Note: the document must be in docx form.

## Directory Structure

```
├── gamechanger-data/common/document_parser/lib/section_parse
│   ├── __init__.py
│   ├── docx_parser.py                 DocxParser class
│   ├── utils
│   │   ├── __init__.py
│   │   ├── sections.py                Sections class
│   │   ├── section_types.py           Helper functions for types of sections that can be added to a Sections object
│   │   └── utils.py
│   ├── tests
│   │   ├── __init__.py
│   │   ├── test_item.py
│   │   ├── data/*
│   │   ├── unit                       Unit Tests
│   │   │   ├── __init__.py
│   │   │   ├── test_sections.py       Unit Tests for sections_parser.utils.sections
│   │   │   ├── test_utils.py          Unit Tests for section_parser.utils.utils
│   │   │   ├── test_docx_parser.py    Unit Tests for section_parser.docx_parser
│   │   ├── integration                Integrated Tests
│   │   │   ├── __init__.py
│   │   │   ├── test_parse.py          Tests for the main function (`DocxParser.parse()`) of this module.
```

## Example Usage

```python
from section_parse import DocxParser

doc = DocxParser(<docx path>)
# file name should be doc type + " " + doc number
sections = doc.parse(<file name>)

for section in sections.sections:
    print(section)

print("Purpose sections:", sections.purpose)
print("Responsibilities sections:", sections.responsibilities)
print("References sections:", sections.references)
```

## How to Convert PDF to Docx

1. Install `pdf2docx`
   ```
   pip install pdf2docx==0.5.5
   ```
2. Use the `parse()` function.

   ```python
    from pdf2docx import parse

    parse(<pdf path>, <docx path>)
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
