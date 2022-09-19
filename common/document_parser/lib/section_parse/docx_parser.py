from docx import Document
from docx.document import Document as _Document
from docx.oxml.text.paragraph import CT_P
from docx.oxml.table import CT_Tbl
from docx.table import _Cell, Table
from docx.text.paragraph import Paragraph
from statistics import mode, StatisticsError
from itertools import chain
from re import search
from typing import Iterator, List, Union
from os import PathLike

from .utils import (
    Sections,
    is_alpha_list_item,
    match_num_list_item,
    is_space,
    should_skip,
    remove_strikethrough_text
)


class DocxParser:
    """Parse a docx document into sections.

    Attributes:
    ----------
        doc (docx.Document): The docx document.

        sections (Sections): Sections of the document. Use parse() to populate.

        blocks (List[docx.text.paragraph.Paragraph|docx.table.Table]): The
            document's paragraphs and tables in order.

        space_mode (int): The most frequent value (not including 0) of space
            before a block.
    """

    def __init__(self, path: Union[str, PathLike]):
        """Parse a docx document into sections.

        Args:
            path (Union[str, PathLike]): Path to the docx document.
        """
        self.doc = Document(path)
        self.sections = Sections()
        self.blocks = list(self.iter_block_items())
        self.space_mode = self.calculate_space_mode(self.blocks)

    def parse(self, fn, should_remove_striken_text=False) -> Sections:
        """Parse a docx document into sections.

        Populates the objects `sections` attribute.

        Args:
            fn (str): File name of the document.
                Use `{doc_type} + " " + {doc_num}`.

        Returns:
            list of lists of str
        """
        self.sections = Sections()

        for block in self.blocks:
            if isinstance(block, Table):
                table_pars = [
                    par
                    for par in self.flatten_table(block)
                    if par.text
                    and not is_space(par.text)
                    and not should_skip(par.text.strip(), fn)
                ]
                if not table_pars:
                    continue
                block = table_pars[0]
                block_texts = [par.text for par in table_pars]
            else:
                if should_remove_striken_text:
                    remove_strikethrough_text(block)
                block_texts = [block.text]

            self.sections.add(block, block_texts, fn, self.space_mode)

        self.sections.combine_by_section_num()
        self.sections.combine_enclosures()
        self.sections.combine_glossary()

        return self.sections

    def iter_block_items(self) -> Iterator[Union[Paragraph, Table]]:
        """Returns an Iterator for the document's paragraphs and tables.

        Generates a reference to each paragraph and table child in document
        order. Each returned value is an instance of either Table or
        Paragraph.

        This is necessary because there is currently no solution within the
        python-docx library to iterate over both paragraphs and tables in order.
        """
        parent = self.doc

        if isinstance(parent, _Document):
            parent_elm = parent.element.body
        elif isinstance(parent, _Cell):
            parent_elm = parent._tc
        else:
            raise ValueError("something's not right")

        for child in parent_elm.iterchildren():
            if isinstance(child, CT_P):
                yield Paragraph(child, parent)
            elif isinstance(child, CT_Tbl):
                yield Table(child, parent)

    @staticmethod
    def flatten_table(table: Table) -> List[Paragraph]:
        """Flatten a Table into Paragraphs."""
        pars = []
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    pars.append(paragraph)

        pars = DocxParser.fix_table_order(pars)
        return pars

    @staticmethod
    def fix_table_order(pars: List[Paragraph]) -> List[Paragraph]:
        """Fix the order of a table's paragraphs.

        Helper function for flatten_table().
        """
        if len(pars) == 2:
            reversed_pars = [pars[1], pars[0]]
            p1_text = pars[0].text.strip()
            p2_text = pars[1].text.strip()

            if (
                (
                    is_alpha_list_item(p2_text)
                    and not is_alpha_list_item(p1_text)
                )
                or (
                    match_num_list_item(p2_text)
                    and not match_num_list_item(p1_text)
                )
                or (p2_text[:1].isupper() and p1_text[:1].islower())
                or search(r"[,:;]", p2_text)
            ):
                return reversed_pars

        return pars

    @staticmethod
    def calculate_space_mode(blocks: List[Union[Paragraph, Table]]) -> int:
        """Get the most frequent value (not including 0) of space before a
        block.

        Args:
            blocks (list of Paragraph|Table): A document's paragraphs and
                tables.

        Returns:
            int
        """
        blocks_flat = list(
            chain.from_iterable(
                [
                    DocxParser.flatten_table(block)
                    if isinstance(block, Table)
                    else [block]
                    for block in blocks
                ]
            )
        )

        space_before = [
            par.paragraph_format.space_before
            for par in blocks_flat
            if par.paragraph_format.space_before is not None
            and par.paragraph_format.space_before != 0
        ]

        try:
            space_mode = mode(space_before)
        except StatisticsError as e:
            print(
                "ERROR calling DocxParser.get_space_mode().",
                e,
                "Returning 0.",
            )
            space_mode = 0

        return space_mode
