from common.document_parser.lib.document import FieldNames
from .parser_definition import ParserDefinition


class USCodeParser(ParserDefinition):
    """Section parser for US Code Title documents.

    Child of ParserDefinition.
    """

    SUPPORTED_DOC_TYPES = ["title"]

    def __init__(self, doc_dict: dict, test_mode: bool = False):
        super().__init__(doc_dict, test_mode)
        self._title = self.doc_dict[FieldNames.TITLE]
        self._doc_num = self.doc_dict[FieldNames.DOC_NUM]

    @property
    def purpose(self):
        return (
            f"Title {self._doc_num} of the United States Code outlines the "
            f"role of {self._title} in the United States Code."
        )
