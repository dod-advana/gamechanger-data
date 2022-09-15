from itertools import chain
from re import search
from docx.text.paragraph import Paragraph
from typing import List
from .utils import (
    get_subsection,
    next_section_num,
    is_next_num_list_item,
    match_enclosure_num,
    match_section_num,
)
from .section_types import (
    should_skip,
    is_same_section_num,
    is_known_section_start,
    is_enclosure_continuation,
    is_child,
)
from .utils import is_space


class Sections:
    """Build and extract document sections."""

    def __init__(self):
        self._sections = []
        # Flags for whether or not the last 3 sections were only whitespace.
        self._prev_spaces = [False, False, False]

    @property
    def sections(self) -> List[List[str]]:
        return self._sections

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
        return self._get_section_by_title("applicability")

    @property
    def policy(self):
        return self._get_section_by_title("policy")

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

    def add(
        self,
        par: Paragraph,
        section_texts: List[str],
        fn: str,
        space_mode: int,
    ) -> None:
        """Add a section to the object's `sections`.

        Uses paragraph formatting and text properties to determine if the
        section is a new section, child/ continuation of the last section,
        or if it should be skipped.

        Args:
            par (Paragraph): Paragraph representation of the section to add.
            section_texts (List[str]): String representations of the section's
                text.
            fn (str): File name of the document section being added.
                Use `{doc_type} + " " + {doc_num}`.
            space_mode (int): Mode value of space before a block.
                See DocxParser.calculate_space_mode().
        """
        text_stripped = par.text.strip()
        is_a_space = is_space(par.text)
        last_section = self._sections[-1] if self._sections else []

        # The order of this is purposeful. Be careful about changing it.
        if is_a_space:
            pass
        elif should_skip(text_stripped, fn):
            pass
        elif all(self._prev_spaces):
            self.add_parent(section_texts)
        elif is_same_section_num(text_stripped, last_section):
            self.add_child(section_texts)
        elif is_enclosure_continuation(text_stripped, last_section):
            self.add_continuation(section_texts[0])
        elif is_known_section_start(text_stripped):
            self.add_parent(section_texts)
        elif is_child(par, last_section, space_mode):
            self.add_child(section_texts)
        else:
            self.add_parent(section_texts)

        self._prev_spaces[2] = self._prev_spaces[1]
        self._prev_spaces[1] = self._prev_spaces[0]
        self._prev_spaces[0] = is_a_space

    def add_parent(self, texts: List[str]) -> None:
        """Add a new parent section to the object's `sections` list."""
        self._sections.append(texts)

    def add_child(self, texts: List[str]) -> None:
        """Add a new child section to the object's `sections` list.

        This section will be added to the end of the last item in the object's
        `sections` list.
        """
        if self._sections:
            self._sections[-1] += texts
        else:
            self._sections.append(texts)

    def add_continuation(self, text: str) -> None:
        """Add the text to the last subsection of the object's `sections` list.

        For example, if a sentence is cut off prematurely, you can add the
        remainder of the sentence with this function.
        """
        if self._sections:
            self._sections[-1][-1] += text
        else:
            self._sections.append([text])

    def combine_sections(self, start: int, end: int) -> None:
        """Combine sections together.

        Updates the object's `sections` attribute.

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

    def combine_glossary(self) -> None:
        """Combine all Glossary sections into 1 section."""
        n_sections = len(self._sections)
        inds = [
            i
            for i in range(n_sections)
            if self._sections[i][0].strip().startswith("GLOSSARY")
        ]
        if not inds:
            return

        if len(inds) == 1:
            end = next(
                (
                    i
                    for i in range(inds[0] + 1, n_sections)
                    if self._sections[i][0].isupper()
                ),
                None,
            )
            if end is None:
                return
            self.combine_sections(min(inds), end - 1)
        else:
            self.combine_sections(min(inds), max(inds))

    def combine_enclosures(self) -> None:
        i = 0
        while i < len(self._sections):
            encl_num = match_enclosure_num(get_subsection(self._sections[i]))
            if encl_num:
                combined_same = self._combine_by_enclosure_num(i, encl_num)
                while combined_same:
                    combined_same = self._combine_by_enclosure_num(i, encl_num)
            i += 1

    def combine_by_section_num(self) -> None:
        """After all sections are added to the object's `sections` list, use
        this function to further combine sections and subsections.

        Examples:
            self.sections = [
                "SECTION 1: blah".
                "some text that should be part of section 1 but wasn't added as
                a child",
                "SECTION 2: hello"
            ] --> combine indices 0 and 1

            self.sections = [
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

    def _combine_by_section_num(
        self, i: int, curr_num: str, max_steps: int = 2
    ) -> bool:
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
        self, i: int, curr_num: str, max_steps: int = 5
    ) -> bool:
        next_enclosure = str(int(curr_num) + 1)
        found_next = False
        end = None

        for j in range(i + 1, i + max_steps + 1):
            if j >= len(self._sections):
                return False
            subsection_j = get_subsection(self._sections[j])
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
            section for section in self.sections if search(pattern, section[0])
        ]
