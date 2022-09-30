from itertools import chain
from typing import List
from common.document_parser.cli import get_default_logger


class ParserDefinition:
    """Base class for section parsers. 

    Attributes:
    -----------
        SUPPORTED_DOC_TYPES (list of str): Document types supported by the 
            parser. To be implemented by child classes. Note: all strings 
            should be lowercase.

        purpose (list of str): Purpose sections of the document.

        responsibilities (list of str): Responsibilities (list of str): sections 
            of the document. 

        subject (list of str): Subject sections of the document.

        references (list of str): References sections of the document.

        procedures (list of str): Procedures sections of the document.

        effective_date (list of str): Effective Date sections of the document.

        applicability (list of str): Applicability sections of the document.

        policy (list of str): Policy sections of the document.

        organizations (list of str): Organizations sections of the document.

        definitions (list of str): Definitions sections of the document.

        authorities (list of str): Authorities sections of the document.

        table_of_contents (list of str): Table of Contents sections of the document.

        glossary (list of str): Glossary sections of the document.

        releasability (list of str): Releasability sections of the document.

        summary of change (list of str): Summary of Change sections of the document.
    """

    SUPPORTED_DOC_TYPES = []

    def __init__(self, doc_dict: dict, test_mode: bool = False):
        self.doc_dict = doc_dict
        self._test_mode = test_mode
        self._sections = []
        self._logger = get_default_logger()

    @property
    def all_sections(self) -> List[List[str]]:
        return self._sections

    @property
    def purpose(self) -> List[str]:
        return []

    @property
    def responsibilities(self) -> List[str]:
        return []

    @property
    def subject(self) -> List[str]:
        return []

    @property
    def references(self) -> List[str]:
        return []

    @property
    def procedures(self) -> List[str]:
        return []

    @property
    def effective_date(self) -> List[str]:
        return []

    @property
    def applicability(self) -> List[str]:
        return []

    @property
    def policy(self) -> List[str]:
        return []

    @property
    def organizations(self) -> List[str]:
        return []

    @property
    def definitions(self) -> List[str]:
        return []

    @property
    def table_of_contents(self) -> List[str]:
        return []

    @property
    def authorities(self) -> List[str]:
        return []

    @property
    def glossary(self) -> List[str]:
        return []

    @property
    def releasability(self) -> List[str]:
        return []

    @property
    def summary_of_change(self) -> List[str]:
        return []

    def add_parent(self, texts: List[str]) -> None:
        """Add a new parent section."""
        self._sections.append(texts)

    def add_child(self, texts: List[str]) -> None:
        """Add a new child section."""
        if self._sections:
            self._sections[-1] += texts
        else:
            self._sections.append(texts)

    def add_continuation(self, text: str) -> None:
        """Add the text to the last subsection.

        For example, if a sentence is cut off prematurely, you can add the
        remainder of the sentence with this function.
        """
        if self._sections:
            self._sections[-1][-1] += text
        else:
            self._sections.append([text])

    def combine_sections(self, start: int, end: int) -> None:
        """Combine sections together.

        Args:
            start (int): First index of the sections to combine.
            end (int): Last index of the sections to combine.

        Raises:
            ValueError: If an invalid start or end is passed.
        """
        if start < 0:
            raise ValueError(f"Bad start: {start}")

        if end >= len(self._sections):
            raise ValueError(f"Bad end: {end}")

        if start > end:
            raise ValueError(
                f"Start cannot be greater than end. start: {start}, end: {end}"
            )

        self._sections[start : end + 1] = [
            list(chain.from_iterable(self._sections[start : end + 1]))
        ]
