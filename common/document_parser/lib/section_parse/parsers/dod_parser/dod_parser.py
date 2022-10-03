from re import search
from os.path import split, splitext
from os import remove
from pdf2docx import parse as convert_pdf_to_docx
from docx.text.paragraph import Paragraph
from docx.table import Table
from typing import List
from common.document_parser.lib.section_parse.utils import DocxParser
from common.document_parser.lib.document import FieldNames
from .utils import (
    get_subsection,
    get_subsection_of_section_1,
    match_attachment_num,
    next_section_num,
    is_next_num_list_item,
    match_enclosure_num,
    match_section_num,
    is_space,
    is_toc,
    starts_with_glossary,
    should_skip,
    is_same_section_num,
    is_known_section_start,
    is_enclosure_continuation,
    is_child,
    remove_strikethrough_text,
)
from ..parser_definition import ParserDefinition


class DoDParser(ParserDefinition):
    """Parse sections of DoD documents."""

    SUPPORTED_DOC_TYPES = ["dodd", "dodi", "dodm"]

    def __init__(self, doc_dict: dict, test_mode: bool = False):
        super().__init__(doc_dict, test_mode)
        self._doc_type = split(self.doc_dict[FieldNames.DOC_TYPE])[1]
        self._doc_num = splitext(self.doc_dict.get(FieldNames.DOC_NUM, ""))[0]
        self._pagebreak_text = " ".join([self._doc_type, self._doc_num])
        # Track the number of previous, consecutive sections that are only
        # whitespace. This is used in _add() to inform about section breaks.
        self._prev_space_count = 0

        if not test_mode:
            self._pdf_path = self.doc_dict.get(FieldNames.PDF_PATH)
            self._docx_path = splitext(self._pdf_path)[0] + ".docx"
            self._parse()

    @property
    def purpose(self):
        return self._get_section_by_title("purpose")

    @property
    def responsibilities(self):
        return self._get_section_by_title("responsibilities")

    @property
    def subject(self):
        return self._get_section_by_title("subject")

    @property
    def references(self):
        return self._get_section_by_title("references")

    @property
    def procedures(self):
        return self._get_section_by_title("procedures")

    @property
    def effective_date(self):
        return self._get_section_by_title("effective date")

    @property
    def applicability(self):
        applicability_section = self._get_section_by_title("applicability")

        # Sometimes the Applicability section is a subsection of Section 1.
        if not applicability_section:
            section_1 = self._get_section_by_num(1)
            applicability_section = get_subsection_of_section_1(
                section_1, "applicability"
            )

        return applicability_section

    @property
    def policy(self):
        policy_section = self._get_section_by_title("policy")

        # Sometimes the Policy section is a subsection of Section 1.
        if not policy_section:
            section_1 = self._get_section_by_num(1)
            policy_section = get_subsection_of_section_1(section_1, "policy")

        return policy_section

    @property
    def organizations(self):
        return self._get_section_by_title("organizations")

    @property
    def definitions(self):
        return self._get_section_by_title("definitions")

    @property
    def table_of_contents(self):
        return self._get_section_by_title("table of contents")

    @property
    def authorities(self):
        return self._get_section_by_title("authorities")

    @property
    def glossary(self):
        return self._get_section_by_title("glossary")

    @property
    def releasability(self):
        return self._get_section_by_title("releasability")

    @property
    def summary_of_change(self):
        return self._get_section_by_title("summary of change")

    def _parse(self, should_remove_strikethrough_text: bool = False) -> None:
        # Convert pdf to docx.
        if not self._test_mode:
            try:
                convert_pdf_to_docx(self._pdf_path, self._docx_path)
            except:
                self._logger.exception(
                    f"Failed to convert pdf to docx: {self._pdf_path}"
                )
                return

        # Create a DocxParser.
        docx_parser = None
        try:
            docx_parser = DocxParser(self._docx_path)
        except:
            self._logger.exception(
                f"Failed to initialize DocxParser: {self._docx_path}"
            )
            return

        # Parse the docx file.
        try:
            for block in docx_parser.blocks:
                if isinstance(block, Table):
                    table_paragraphs = [
                        remove_strikethrough_text(par)
                        if should_remove_strikethrough_text
                        else par
                        for par in docx_parser.flatten_table(block)
                        if par.text
                        and not is_space(par.text)
                        and not should_skip(
                            par.text.strip(), self._pagebreak_text
                        )
                    ]
                    if not table_paragraphs:
                        continue
                    block = table_paragraphs[0]
                    block_texts = [par.text for par in table_paragraphs]
                else:
                    if should_remove_strikethrough_text:
                        remove_strikethrough_text(block)
                    block_texts = [block.text]
                self._add(block, block_texts, docx_parser.space_mode)
            self._combine_section_nums()
            self._combine_enclosures()
            self._combine_attachments()
            self._combine_glossary()
            self._remove_repeated_section_titles()
        except:
            self._logger.exception(
                f"Failed to parse sections of docx document: {self._docx_path}."
            )
        else:
            remove(self._docx_path)

    def _add(
        self,
        par: Paragraph,
        section_texts: List[str],
        space_mode: int,
    ) -> None:
        """Add a section.

        Uses paragraph formatting and text properties to determine if the
        section is a new section, child/ continuation of the last section,
        or if it should be skipped.

        Args:
            par (Paragraph): Paragraph representation of the section to add.
            section_texts (List[str]): String representations of the section's
                text.
            space_mode (int): Mode value of space before a block.
                See DocxParser.calculate_space_mode().
        """
        text_stripped = par.text.strip()
        is_a_space = is_space(par.text)
        last_section = self._sections[-1] if self._sections else []

        # The order of this is purposeful. Be careful about changing it.
        if is_a_space:
            pass
        elif should_skip(text_stripped, self._pagebreak_text):
            pass
        # If 3 previous paragraphs are only space, the text is probably a new
        # section because it's probably on a new page.
        elif self._prev_space_count >= 3:
            self.add_parent(section_texts)
        elif is_same_section_num(text_stripped, last_section):
            self.add_child(section_texts)
        elif is_enclosure_continuation(text_stripped, last_section):
            self.add_continuation(section_texts[0])
        elif is_known_section_start(text_stripped, par):
            self.add_parent(section_texts)
        # This can have false positives if the other conditions aren't checked
        # first.
        elif is_child(par, last_section, space_mode):
            self.add_child(section_texts)
        else:
            self.add_parent(section_texts)

        self._update_prev_space_count(is_a_space)

    def _combine_glossary(self) -> None:
        """Combine all Glossary parts into 1 section.

        According to the DoD Issuance Style Guide, "A glossary is mandatory for
        all issuances over two pages that define terms and/or establish acronyms.
        It is always the second to last section in an issuance, followed only
        by the Reference section. It is broken up into two parts, 'G1. Acronyms'
        and 'G2. Definitions'... If you define terms but don't use any acronyms
        (or vice versa), delete the part you don't need from the template.
        Remove 'G.1.' or 'G.2.' and the paragraph title, so the Glossary is
        only listed as 'Glossary' followed by the acronym or definition terms,
        as appropriate".
        """
        n_sections = len(self._sections)
        glossary_inds = [
            i
            for i in range(n_sections)
            if starts_with_glossary(get_subsection(self._sections[i]))
        ]
        if not glossary_inds:
            return

        if len(glossary_inds) == 1:
            end = None
            ref_inds = [
                i
                for i in range(n_sections)
                if get_subsection(self._sections[i]).startswith("REFERENCES")
            ]

            # If a References section comes after the Glossary, then the end
            # of the Glossary is before the start of that References section.
            if ref_inds:
                last_ref_ind = ref_inds[-1]
                if last_ref_ind > glossary_inds[0] + 1:
                    end = last_ref_ind - 1
            # If there is no References section after the Glossary section,
            # then the end of the Glossary section is the end of the document.
            else:
                end = len(self._sections)

            if end is None:
                return
            self.combine_sections(min(glossary_inds), end - 1)
        else:
            self.combine_sections(min(glossary_inds), max(glossary_inds))

    def _combine_enclosures(self) -> None:
        i = 0
        while i < len(self._sections):
            encl_num = match_enclosure_num(get_subsection(self._sections[i]))
            if encl_num:
                combined_same = self._combine_by_enclosure_num(i, encl_num)
                while combined_same:
                    combined_same = self._combine_by_enclosure_num(i, encl_num)
            i += 1

    def _combine_attachments(self) -> None:
        i = 0
        while i < len(self._sections):
            encl_num = match_attachment_num(get_subsection(self._sections[i]))
            if encl_num:
                combined_same = self._combine_by_enclosure_num(
                    i, encl_num, enclosure_as_attachment=True
                )
                while combined_same:
                    combined_same = self._combine_by_enclosure_num(
                        i, encl_num, enclosure_as_attachment=True
                    )
            i += 1

    def _combine_section_nums(self) -> None:
        """After all sections are added to the object's `sections` list, use
        this function to further combine sections and subsections.

        Examples:
            self.all_sections = [
                "SECTION 1: blah".
                "some text that should be part of section 1 but wasn't added as
                a child",
                "SECTION 2: hello"
            ] --> combine indices 0 and 1

            self.all_sections = [
                "SECTION 3: hi",
                "SECTION 4: blah",
                "SECTION 4: blah blah",
                "SECTION 5: hey"
            ] --> combine indices 1 and 2
        """
        i = 0
        while i < len(self._sections):
            curr_num = match_section_num(get_subsection(self._sections[i]))
            if curr_num:
                go = self._combine_by_section_num(i, curr_num)
                while go:
                    go = self._combine_by_section_num(i, curr_num)
            i += 1

    def _remove_repeated_section_titles(self) -> None:
        """Remove repeated section titles from within section bodies.

        Section titles are often repeated when a section spans over multiple
        pages, since the title is restated on each page.

        This function makes each title only appear once, as the first item in
        each section.
        """
        for i in range(len(self._sections)):
            first_subsection = get_subsection(self._sections[i])
            toc = is_toc(first_subsection)

            if not toc and starts_with_glossary(first_subsection):
                self._sections[i][1:] = [
                    subsection
                    for subsection in self._sections[i][1:]
                    if not starts_with_glossary(subsection.strip())
                ]
                continue

            enclosure_num = match_enclosure_num(first_subsection)
            if not toc and enclosure_num:
                self._sections[i][1:] = [
                    subsection
                    for subsection in self._sections[i][1:]
                    if not match_enclosure_num(
                        subsection.strip(), enclosure_num
                    )
                ]
                continue

            self._sections[i][1:] = [
                subsection
                for subsection in self._sections[i][1:]
                if subsection.strip().lower() != first_subsection.lower()
            ]

    def _get_section_by_title(self, words: str) -> List[List[str]]:
        # Note: don't include special regex chars in words
        if len(words) == 0:
            raise ValueError("word arg cannot be an empty string.")

        words = words.split(" ")

        pattern = r"\b"
        for word in words:
            pattern += rf"{word[:1].upper()}(?:{word[1:].lower()}|{word[1:].upper()})\s+"
        pattern = pattern.rstrip(r"\s+")
        pattern += r"\b"

        return [
            section
            for section in self._sections
            if search(pattern, section[0])
        ]

    def _get_section_by_num(self, section_num: int) -> List[List[str]]:
        section_num = str(section_num)

        return next(
            (
                s
                for s in self._sections
                if match_section_num(s[0], section_num)
            ),
            [],
        )

    def _combine_by_section_num(
        self, i: int, curr_num: str, max_steps: int = 2
    ) -> bool:
        """Helper for combine_section_nums()."""
        next_num = next_section_num(curr_num)
        found_next = False
        end = None

        for j in range(i + 1, i + max_steps + 1):
            if j >= len(self._sections):
                return False
            num_j = match_section_num(get_subsection(self._sections[j]))
            if num_j is not None:
                if num_j == curr_num:
                    end = j
                    break
                elif num_j == next_num:
                    if j == i + 1:
                        break
                    end = j - 1
                    found_next = True
                    break

        if end is not None:
            self.combine_sections(i, end)
            if found_next:
                return False
            return True

        return False

    def _combine_by_enclosure_num(
        self,
        i: int,
        curr_num: str,
        max_steps: int = 5,
        enclosure_as_attachment: bool = False,
    ) -> bool:
        """Helper for _combine_enclosures()"""
        next_enclosure = str(int(curr_num) + 1)
        found_next = False
        end = None

        for j in range(i + 1, i + max_steps + 1):
            if j >= len(self._sections):
                return False
            subsection_j = get_subsection(self._sections[j])

            if enclosure_as_attachment:
                enclosure_j = match_attachment_num(subsection_j)
            else:
                enclosure_j = match_enclosure_num(subsection_j)

            if enclosure_j:
                if enclosure_j == curr_num:
                    end = j
                    break
                elif enclosure_j == next_enclosure:
                    if j == i + 1:
                        break
                    else:
                        end = j - 1
                        found_next = True
                        break
                else:
                    break
            else:
                if is_next_num_list_item(subsection_j, self._sections[i]):
                    end = j
                    break

        if end is not None:
            self.combine_sections(i, end)
            # Return False if the next enclosure number was found so that we
            # move on to the next index.
            if found_next:
                return False
            return True

        return False

    def _update_prev_space_count(self, is_space: bool) -> None:
        if is_space:
            self._prev_space_count += 1
        else:
            self._prev_space_count = 0
