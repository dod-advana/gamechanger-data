# Section Parsing

## Directory Structure

```
gamechanger-data/common/document_parser/lib/section_parse/

├── __init__.py
├── add_sections.py                Add document sections to a doc dict. Used in the policy analytics pipeline
├── parsers
│   ├── __init__.py
│   ├── parser_factory.py          ParserFactory class. Determines the parser to create for a given document
│   ├── parser_definition.py       ParserDefinition class. Base class for all section parsers
│   ├── dod_parser.py              DoDParser class
├── utils
│   ├── __init__.py
│   └── dod_utils.py               Utils for DoDParser
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
