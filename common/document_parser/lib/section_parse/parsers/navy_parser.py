from re import search, IGNORECASE, finditer, compile, finditer, RegexFlag
from os.path import basename
from typing import List
from common.document_parser.lib.document import FieldNames
from typing import List
from .parser_definition import ParserDefinition
from .utils import (
    match_number_hyphenated_section,
    get_letter_dot_section,
    match_number_dot_section,
)


class NavyParser(ParserDefinition):

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
        self._filename = basename(self.doc_dict[FieldNames.FILENAME])
        self._text = self.get_raw_text()

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
                purposes = [
                    get_letter_dot_section(situation[0], "purpose")
                ]

        return purposes

    @property
    def policy(self):
        return self._get_numbered_section_with_name("policy")

    @property
    def responsibilities(self):
        resp = self._get_numbered_section_with_name("responsibilit(?:y|ies)", False)
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
        """Get a numbered section with the given section name.

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
            first_num = start_match.groups()[0]
            second_num = "".join(
                char for char in start_match.groups()[1] if char.isdigit()
            )
            cropped_text = self._text[start_match.start() :]

            if second_num:
                end_match = match_number_hyphenated_section(
                    cropped_text, first_num, str(int(second_num) + 1)
                )
                if not end_match:
                    end_match = match_number_hyphenated_section(
                        cropped_text, str(int(first_num) + 1)
                    )
            else:
                end_match = match_number_dot_section(
                    cropped_text, str(int(first_num) + 1)
                )

            if end_match:
                sections.append(cropped_text[: end_match.start()])
            else:
                sections.append(cropped_text)

        return sections
