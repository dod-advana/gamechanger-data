# Section Parsing

This module supports parsing DoD documents into sections. Note: the document must be in docx form.

## Directory Structure

```
├── gamechanger-data/common/document_parser/lib/section_parse
│   ├── __init__.py
│   ├── docx_parser.py              DocxParser class
│   ├── utils
│   │   ├── __init__.py
│   │   ├── sections.py             Sections class
│   │   ├── section_types.py        Helper functions for types of sections that can be added to a Sections object
│   │   └── utils.py
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
