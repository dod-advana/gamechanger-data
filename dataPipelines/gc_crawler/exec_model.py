# -*- coding: utf-8 -*-
"""
gc_crawler.exec_model
-----------------
Classes that define main parts of gc_crawler exec flow
"""

from abc import ABC, abstractmethod
from typing import Iterable, Tuple
from .requestors import Requestor, DefaultRequestor
from .data_model import Document
from .validators import DefaultOutputSchemaValidator, SchemaValidator


#####
# CRAWLER EXEC MODEL
#####


class Pager(ABC):
    """Iterates pages on which publication objects are located
    :param starting_url: url from which page navigation starts
    :param requestor: shared web requestor
    """

    def __init__(self, starting_url: str, requestor: Requestor = DefaultRequestor()):
        self.starting_url = starting_url
        self.requestor = requestor

    @abstractmethod
    def iter_page_links(self) -> Iterable[str]:
        """Iterator for page links"""
        pass

    def iter_page_links_with_text(self) -> Iterable[Tuple[str, str]]:
        """Iterator for page links accompanied by their text"""
        for link in self.iter_page_links():
            yield link, self.requestor.get_text(link)


class Parser(ABC):
    """Parses pages for Document objects"""

    @abstractmethod
    def parse_docs_from_page(self, page_url: str, page_text: str) -> Iterable[Document]:
        """Parses Document objects from a single page of text"""
        pass


class Crawler:
    """Combines all other exec model classes to produce final crawler output
    :param pager: web page text iterator
    :param parser: page to document object parser
    :param validator: crawler output validator"""

    def __init__(
        self,
        pager: Pager,
        parser: Parser,
        validator: SchemaValidator = DefaultOutputSchemaValidator(),
    ):

        # required arg preconditions
        if not isinstance(pager, Pager):
            raise TypeError("arg: pager must be of type Pager")
        if not isinstance(parser, Parser):
            raise TypeError("arg: parser must be of type Parser")
        if not isinstance(validator, SchemaValidator):
            raise TypeError("arg: validator must be of type SchemaValidator")

        # set vars
        self._pager = pager
        self._parser = parser
        self._validator = validator

    def iter_output_docs(self) -> Iterable[Document]:
        """iterates through docs returned by the parser"""
        for (page_link, page_text) in self._pager.iter_page_links_with_text():
            for doc in self._parser.parse_docs_from_page(page_link, page_text):
                yield doc

    def iter_output_json(self) -> Iterable[str]:
        """Iterates through json-serialized docs returned by the parser"""
        for doc in self.iter_output_docs():
            yield doc.to_json()

    def iter_validated_output_json(self) -> Iterable[str]:
        """returned json-serialized docs from parser unless schema validation fails"""
        for json_doc in self.iter_output_json():
            self._validator.validate(json_doc)
            yield json_doc
