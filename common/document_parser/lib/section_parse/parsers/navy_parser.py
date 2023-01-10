from re import search, IGNORECASE, VERBOSE, compile, finditer, RegexFlag
from os.path import splitext
from typing import List
from .parser_definition import ParserDefinition
from .utils import (
    match_number_hyphenated_section,
    get_letter_dot_section,
    match_number_dot_section,
    match_first_appendix_title,
    remove_pagebreaks,
    DD_MONTHNAME_YYYY,
)


class NavyParser(ParserDefinition):
    """Section parser for Navy document types (see SUPPORTED_DOC_TYPES).

    Child of ParserDefinition.
    """

    SUPPORTED_DOC_TYPES = [
        "opnavinst",
        "opnavnote",
        "bumedinst",
        "milpersman",
        "respersman",
        "bupersinst",
        "secnavinst",
        "secnavnote",
        "mco",
        "navmc",
        "comnavresforcominst",
        "comnavresforcomnote",
        "bumednote",
        "alnav",
        "mcrp",
        "mcbul",
        "fmfrp",
    ]

    def __init__(self, doc_dict: dict, test_mode: bool = False):
        super().__init__(doc_dict, test_mode)
        self._text = self.get_raw_text()
        self._filename_without_extension = splitext(self._filename)[0]

    @property
    def purpose(self):
        purposes = self._get_numbered_section_with_name("purpose", False)
        # In some document types, a "Situation" section is used in place of a
        # "Purpose" section.
        if not purposes and self._doc_type.lower() == "mcbul":
            # In some MCBUL documents, the purpose section is nested within
            # the situation section.
            situation = self._get_numbered_section_with_name("situation")
            if situation:
                purposes = [get_letter_dot_section(situation[0], "purpose")]

        return purposes

    @property
    def policy(self):
        return self._get_numbered_section_with_name("policy")

    @property
    def responsibilities(self):
        resp = self._get_numbered_section_with_name(
            "responsibilit(?:y|ies)", False
        )

        if not resp:
            # Examples of unique responsibilities sections:
            #    "\n3.  Records Responsibilities. "
            #    "\4.  Assignment Responsibility. "
            resp = self._get_numbered_section_with_name(
                ".{0,30}R(?:esponsibilit(?:y|ies)|ESPONSIBILIT(?:Y|IES))",
                False,
                [],
            )
        return resp

    def _get_numbered_section_with_name(
        self,
        section_name: str,
        first_only: bool = True,
        regex_flags: List[RegexFlag] = [IGNORECASE],
    ) -> List[str]:
        """Get a numbered section with the given section name or pattern.

        Args:
            section_name (str): Name of the section to get
            first_only (bool, optional): True to get only the first numbered
                section with the given section name, False to get all of them.
                Defaults to True.
            regex_flags (list of RegexFlag, optional): Flags to use in the
                regex search. Defaults to [IGNORECASE].

        Returns:
            list of str
        """
        flags = 0
        for flag in regex_flags:
            flags |= flag

        pattern = compile(
            rf"[\n]([0-9]+)\s*(\.|(-[0-9]{{1,2}}\s*\.?))\s*{section_name}",
            flags=flags,
        )

        if first_only:
            matches = [search(pattern, self._text)]
        else:
            matches = finditer(pattern, self._text)

        sections = []
        if matches == [None]:
            return sections

        for start_match in matches:
            end_match = None
            first_num = start_match.groups()[0]
            second_num = "".join(
                char for char in start_match.groups()[1] if char.isdigit()
            )
            cropped_text = self._text[start_match.start() :]

            if second_num:
                end_match = match_number_hyphenated_section(
                    cropped_text, first_num, {str(int(second_num) + 1)}
                )
                if not end_match:
                    end_match = match_number_hyphenated_section(
                        cropped_text, rf"0?{str(int(first_num) + 1)}"
                    )
            else:
                end_match = match_number_dot_section(
                    cropped_text, rf"0?{str(int(first_num) + 1)}"
                )

            appendix_match = match_first_appendix_title(cropped_text)
            if appendix_match:
                # Use the appendix title match as the end match if it comes
                # before the current end match.
                if end_match and appendix_match.start() < end_match.start():
                    end_match = appendix_match
                # Use the appendix title match as the end match if no other end
                # match was found.
                elif not end_match:
                    end_match = appendix_match

            if end_match:
                sections.append(cropped_text[: end_match.start()])
            else:
                sections.append(cropped_text)

        sections = [self._remove_pagebreaks(section) for section in sections]

        return sections

    def _remove_pagebreaks(self, text: str) -> str:
        text = remove_pagebreaks(
            text, self._filename_without_extension.replace(" ", r"[ ]")
        )
        text = remove_pagebreaks(text, DD_MONTHNAME_YYYY, [VERBOSE])
        text = remove_pagebreaks(text, r"[0-9]{1,3}")  # Page numbers
        return text
