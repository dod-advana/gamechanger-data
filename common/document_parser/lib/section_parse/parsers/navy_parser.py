from re import search
from typing import List
from .parser_definition import ParserDefinition
from common.document_parser.lib.document import FieldNames


class NavyParser(ParserDefinition):

    SUPPORTED_DOC_TYPES = ["opnavinst", "opnavnote", "bumedinst"]

    def __init__(self, doc_dict: dict, test_mode: bool = False):
        super().__init__(doc_dict, test_mode)
        self._text = self.doc_dict[FieldNames.TEXT]

    @property
    def purpose(self) -> List[str]:
        start_match = search(
            r"(?:\n1\s*\.\s*P(?:urpose|URPOSE)\b)", self._text
        )
        if not start_match:
            return []

        start_index = start_match.start()
        end_match = search(r"\n2\s*\.", self._text[start_index:])

        if not end_match:
            return []

        return self._text[start_index : end_match.end()]
