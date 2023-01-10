from os.path import splitext
from re import match, search, fullmatch, IGNORECASE
from typing import List
from .parser_definition import ParserDefinition
from .utils import (
    find_pagebreak_date,
    is_toc,
    is_sentence_continuation,
    match_section_num,
    next_section_num,
    is_known_section_start,
    starts_with_glossary,
    match_enclosure_num,
    get_subsection_of_section_1,
    match_alpha_list_item,
    match_ref_start,
)


class DoDParser(ParserDefinition):
    """Parse a DoD document into sections."""

    SUPPORTED_DOC_TYPES = ["dodd", "dodi", "dodm"]

    def __init__(self, doc_dict: dict, test_mode: bool = False):
        super().__init__(doc_dict, test_mode)
        self._set_pagebreak_text()
        if not self.test_mode:
            self._parse()

    @property
    def all_sections(self) -> List[str]:
        return ["\n".join(s) for s in self._sections]

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
        applicability_section = [
            section.split("\n")
            for section in self._get_section_by_title("applicability")
        ]

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

    def _parse(self) -> None:
        raw_text = self.get_raw_text()
        if not raw_text:
            return

        self._sections = [[line] for line in raw_text.split("\n")]
        self._combine_toc()
        self._remove_pagebreaks_and_noise()
        self._combine_enclosure_titles()
        self._combine_sentence_continuations()
        self._combine_alpha_list_items()
        self._combine_reference_list()
        self._combine_by_section_nums()
        self._combine_enclosures()
        self._combine_glossary_then_references()
        self._remove_repeated_section_titles()
        self._combine_enclosures_list()

    def _set_pagebreak_text(self):
        doc_num = match(
            r"DoD[IMD] ((?:[A-Z]-)?[1-9][0-9]{3}(?:\.[0-9]{1,2}))",
            self._filename,
        )

        if doc_num:
            self._pagebreak_text = " ".join([self._doc_type, doc_num.groups()[0]])
        else:
            self._logger.warning(
                f"Document number not found in filename: `{self._filename}`. "
                "Section parsing results may be adversely affected."
            )
            self._pagebreak_text = splitext(self._filename)[0]

    def _get_section_by_title(self, title_words: str) -> List[str]:
        # Note: don't include special regex chars in title_words
        if len(title_words) == 0:
            raise ValueError("title_word arg cannot be an empty string.")

        title_words = title_words.split(" ")

        pattern = r"\b"
        for word in title_words:
            pattern += rf"{word[:1].upper()}(?:{word[1:].lower()}|{word[1:].upper()})\s+"
        pattern = pattern.rstrip(r"\s+")
        pattern += r"\b"

        return [
            "\n".join(section)
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

    def _combine_toc(self) -> None:
        """Updates self._sections so that all lines of the Table of Contents 
        are combined.

        Example:
        [
            ["TABLE OF CONTENTS "],
            ["SECTION 1:  GENERAL ISSUANCE INFORMATION ............... 3 "],
            ["1.1.  Applicability. ............... 3 "],
            ["1.2.  Policy. ............... 3 "],
            ["1.3.  Information Collections. ............... 3 "],
            ["SECTION 2:  RESPONSIBILITIES ............... 4 "],
            ["2.1.  Assistant Secretary of Defense for Health Affairs (ASD(HA)). ............... 4 "],
            ["2.2.  DASD(HSP&O). ............... 4 "],
            ["2.3.  ATSD(PA). ............... 5 "],
            ["2.4.  Secretaries of the Military Departments. ............... 5 "],
            ["SECTION 3:  SCAADL PROGRAM IMPLEMENTATION GUIDANCE ............... 6 "],
            ["SECTION 1:  GENERAL ISSUANCE INFORMATION "]
        ]
        -->
        [
            [
                "TABLE OF CONTENTS ",
                "SECTION 1:  GENERAL ISSUANCE INFORMATION ............... 3 ",
                "1.1.  Applicability. ............... 3 ",
                "1.2.  Policy. ............... 3 ",
                "1.3.  Information Collections. ............... 3 ",
                "SECTION 2:  RESPONSIBILITIES ............... 4 ",
                "2.1.  Assistant Secretary of Defense for Health Affairs ............... 4 ",
                "2.2.  DASD(HSP&O). ............... 4 ",
                "2.3.  ATSD(PA). ............... 5 ",
                "2.4.  Secretaries of the Military Departments. ............... 5 ",
                "SECTION 3:  SCAADL PROGRAM IMPLEMENTATION GUIDANCE ............... 6 "
            ],
            ["SECTION 1:  GENERAL ISSUANCE INFORMATION "]
        ]
        """
        first_toc_ind = next(
            (
                i
                for i in range(self.num_of_sections)
                if is_toc(self._sections[i][0])
            ),
            None,
        )
        if first_toc_ind is not None:
            last_toc_ind = next(
                (
                    i
                    for i in range(self.num_of_sections - 1, first_toc_ind, -1)
                    if is_toc(self._sections[i][0])
                ),
                None,
            )
            if last_toc_ind is not None:
                self.combine_sections(first_toc_ind, last_toc_ind)

    def _remove_pagebreaks_and_noise(self):
        """Updates self._sections so headers, footers, and other pagebreak texts 
        are removed.
        """
        all_sections = []

        for section in self._sections:
            clean_section = []
            for subsection in section:
                clean_subsection = self._remove_pagebreak(subsection.strip())
                if not self._should_skip(clean_subsection):
                    clean_section.append(subsection)
            if clean_section:
                all_sections.append(clean_section)

        self._sections = all_sections

    def _combine_enclosure_titles(self):
        """Updates self._sections so that individual lines of an Enclosure title 
        are combined.

        Example:
            [
                ["ENCLOSURE 1 "],
                ["RESPONSIBILITIES]
            ]
            -->
            [
                ["ENCLOSURE 1 RESPONSIBILITIES"]
            ]
        """
        i = 0
        while i < self.num_of_sections - 1:
            section_1 = self._sections[i]
            section_2 = self._sections[i + 1]

            if len(section_1) == 1 and len(section_2) > 0:
                section_1_sub = section_1[0].strip()
                section_2_sub = section_2[0].strip()
                if is_toc(section_1_sub) or not any(
                    c.isalpha() for c in section_1_sub
                ):
                    i += 1
                    continue
                elif (
                    is_toc(section_2_sub)
                    or len(section_2_sub) < 4
                    or not any(c.isalpha() for c in section_1_sub)
                ):
                    i += 2
                    continue

                section_1_enclosure = match_enclosure_num(section_1_sub)
                section_2_enclosure = match_enclosure_num(section_2_sub)

                if section_1_enclosure:
                    if section_2_enclosure:
                        if section_1_sub == section_2_sub:
                            del self._sections[i]
                            continue
                        elif section_1_enclosure == section_2_enclosure:
                            self.combine_sections(i, i + 1)
                    elif section_2_sub.isupper():
                        self._sections[i][0] = section_1[0] + section_2[0]
                        self._sections[i] += section_2[1:]
                        del self._sections[i + 1]
                        continue

            i += 1

    def _combine_sentence_continuations(self):
        """Updates self._sections so that improperly split sentences are 
        combined.

        See comments in is_sentence_continuation() for examples.
        """
        i = 1
        while i < self.num_of_sections:
            if is_sentence_continuation(
                self._get_subsection(i, 0, False),
                self._get_subsection(i - 1, -1, False),
            ):
                self._sections[i - 1][-1] += "".join(self._sections[i])
                del self._sections[i]
            else:
                i += 1

    def _combine_alpha_list_items(self):
        """Updates self._sections so that lines of alphabetical lists are 
        combined.

        Example:
            [ 
                ["This Directive: "],
                ["a.  Establishes policy and assigns responsibilities for DSCA. "],
                ["b.  Incorporates and cancels DoD Directive (DoDD) 3025.1 and DoDD 3025.15. "],
                ["c.  Provides guidance for implementing the regulations "],
                ["(in DoD Instruction (DoDI) 3025.21) "],
                ["d.  Provides guidance for the execution and oversight of DSCA"]
                ["REFERENCES:"]
            ]
            -->
            [
                ["This Directive: "],
                [
                    "a.  Establishes policy and assigns responsibilities for DSCA. ",
                    "b.  Incorporates and cancels DoD Directive (DoDD) 3025.1 and DoDD 3025.15. ",
                    "c.  Provides guidance for implementing the regulations ",
                    "(in DoD Instruction (DoDI) 3025.21) ",
                    "d.  Provides guidance for the execution and oversight of DSCA"
                ],
                ["REFERENCES:]
            ]
        """
        i = 0

        while i < self.num_of_sections:
            curr_subsection = self._get_subsection(i)
            curr_letter, curr_func = match_alpha_list_item(curr_subsection)

            if not curr_letter or not curr_func:
                i += 1
                continue

            j = i + 1
            while j - i < 5 and j < self.num_of_sections:
                next_subsection = self._get_subsection(j)
                next_letter, next_func = match_alpha_list_item(next_subsection)
                if next_letter and next_func:
                    if next_func == curr_func:
                        self.combine_sections(i, j)
                        j = i + 1
                    else:
                        break
                elif (
                    match(r"[1-9][0-9]?\.\s", next_subsection)
                    or is_known_section_start(next_subsection)
                    or match_section_num(next_subsection) is not None
                ):
                    break
                else:
                    j += 1

            i += 1

    def _combine_reference_list(self):
        """Updates self._sections so that lines of the References section are
        combined.
        """
        # Combine the References section title with the References list.
        i = 0
        while i < self.num_of_sections - 1:
            curr_subsection = self._get_subsection(i)
            ref_match = match_ref_start(curr_subsection)
            if ref_match:
                curr_letter, curr_func = match_alpha_list_item(
                    curr_subsection[ref_match.end() :].strip()
                )
                next_letter, next_func = match_alpha_list_item(
                    self._get_subsection(i + 1)
                )
                if not next_letter or not next_func:
                    break

                # If there is a letter list item in curr_subsection and the
                # next section, only combine them if they are of the same
                # format (check by comparing *_func).
                if curr_letter:
                    if next_func == curr_func:
                        self.combine_sections(i, i + 1)
                else:
                    self.combine_sections(i, i + 1)

                break
            i += 1

    def _combine_by_section_nums(self):
        """Updates self._sections so that each numbered section's lines are 
        combined.

        Example:
        [
            ["SECTION 1:  GENERAL ISSUANCE INFORMATION "],
            ["1.1.  APPLICABILITY.  This issuance..."],
            ["1.2.  POLICY.  It is DoD policy that..."],
            ["In accordance with..."],
            ["SECTION 2:  RESPONSIBILITIES "],
            ["2.1.  ASSISTANT SECRETARY OF.."],
            ["Under the authority, direction..."],
            ["Readiness, the ASD(HA)..."],
            ["SECTION 3: PROGRAM IMPLEMENTATION GUIDANCE "],
        ]
        -->
        [
            [
                "SECTION 1:  GENERAL ISSUANCE INFORMATION ",
                "1.1.  APPLICABILITY.  This issuance...",
                "1.2.  POLICY.  It is DoD policy that...",
                "1.3.  GUIDELINES.  Each..."
            ]
            [
                "SECTION 2:  RESPONSIBILITIES ",
                "2.1.  ASSISTANT SECRETARY OF..",
            ],  
            [
                "SECTION 3: PROGRAM IMPLEMENTATION GUIDANCE"
            ]
        ]
        """
        i = 0
        while i < self.num_of_sections:
            curr_num = match_section_num(self._get_subsection(i))

            if curr_num:
                j = i + 1
                next_num = next_section_num(curr_num)

                while j < self.num_of_sections - 1:
                    subsection_j = self._get_subsection(j)

                    if match_section_num(subsection_j, next_num):
                        self.combine_sections(i, j - 1)
                        break

                    subsection_j = self._remove_pagebreak(subsection_j)
                    if (
                        not is_toc(subsection_j)
                        and is_known_section_start(subsection_j)
                        # Sometimes the Responsibilities section has a Policy
                        # subsection.
                        and match(r"P(?:olicy|OLICY)", subsection_j) is None
                    ):
                        self.combine_sections(i, j - 1)
                        break
                    else:
                        j += 1

            i += 1

    def _combine_enclosures(self):
        """Updates self._sections so that each Enclosure's lines are combined.

        Example:
            [
                ["6.  EFFECTIVE DATE..."],
                ["E1.  ENCLOSURE 1 "],
                ["REFERENCES, continued "],
                ["(e) DoD Directive 8100.1"],
                ["(f) Chairman of the Joint..."],
                ["E2.  ENCLOSURE 2 "],
                ["DEFINITIONS"],
                ["E2.1.1.  Capability Area...."],
                ["capability delegation, and analysis. "],
                ["E2.1.2.  Enterprise...."],
                ["GLOSSARY"],
            ]
            -->
            [
                ["6.  EFFECTIVE DATE..."],
                [
                    "E1.  ENCLOSURE 1 ",
                    "REFERENCES, continued ",
                    "(e) DoD Directive 8100.1",
                    "(f) Chairman of the Joint..."
                ],
                [
                    "E2.  ENCLOSURE 2 ",
                    "DEFINITIONS",
                    "E2.1.1.  Capability Area....",
                    "capability delegation, and analysis. ",
                    "E2.1.2.  Enterprise...."
                ],
                ["GLOSSARY"],
            ]
        """
        i = 0
        while i < self.num_of_sections:
            curr_subsection = self._get_subsection(i)
            curr_enclosure_num = match_enclosure_num(curr_subsection)

            if curr_enclosure_num:
                next_enclosure_num = str(int(curr_enclosure_num) + 1)

                j = i + 1
                last_ind = None
                while j < self.num_of_sections:
                    next_subsection = self._get_subsection(j)
                    if next_subsection == "GLOSSARY":
                        last_ind = j - 1
                        break
                    next_enclosure = match_enclosure_num(next_subsection)
                    if next_enclosure:
                        if next_enclosure == next_enclosure_num:
                            last_ind = j - 1
                            break
                        elif next_enclosure == curr_enclosure_num:
                            last_ind = j
                        else:
                            break
                    j += 1

                if last_ind is not None:
                    self.combine_sections(i, last_ind)

            i += 1

    def _combine_enclosures_list(self):
        """Updates self._sections so that the lines of an Enclosures list are 
        combined.

        Some documents have a list of all Enclosure that they contain.

        Example:
        [
            ["Enclosures "],
            ["1.  References "],
            ["2.  Responsibilities "],
            ["3.  Procedures "],
            ["Glossary "],
            ["ENCLOSURE 1"],
        ]
        -->
        [
            [
                "Enclosures ",
                "1.  References ",
                "2.  Responsibilities ",
                "3.  Procedures ",
                "Glossary "
            ],
            ["ENCLOSURE 1"]
        ]
        """
        start_ind = next(
            (
                i
                for i in range(self.num_of_sections - 1)
                if len(self._sections[i]) == 1
                and fullmatch(
                    r"E(nclosures|NCLOSURES)(?:.{1,4}[1-9][0-9]?)?",
                    self._get_subsection(i),
                )
            ),
            None,
        )

        if start_ind is None or len(self._sections[start_ind + 1]) != 1:
            return

        next_subsection = self._get_subsection(start_ind + 1)
        end_ind = None

        enclosure_num = match_enclosure_num(next_subsection, "1")
        if enclosure_num:
            end_ind = start_ind + 1
            for i in range(start_ind + 2, self.num_of_sections):
                enclosure_num = str(int(enclosure_num) + 1)
                if len(self._sections[i]) != 1 or not match_enclosure_num(
                    self._get_subsection(i), enclosure_num
                ):
                    end_ind = i - 1
                    break

            self.combine_sections(start_ind, end_ind)
            return

        num_dot = match(r"1\.\s", next_subsection)
        if num_dot:
            num_dot = "1"
            end_ind = start_ind + 1
            for i in range(start_ind + 2, self.num_of_sections):
                num_dot = str(int(num_dot) + 1)
                has_1_subsection = len(self._sections[i]) == 1
                subsection = self._get_subsection(i)
                if has_1_subsection and subsection == "Glossary":
                    end_ind = i
                    break
                elif not has_1_subsection or not match(
                    rf"{num_dot}\.\s", subsection
                ):
                    end_ind = i - 1
                    break
            self.combine_sections(start_ind, end_ind)

    def _combine_glossary_then_references(self):
        """Updates self._sections so that lines of the Glossary are combined 
        into a single section, and lines of the References section are combined
        into a single section.

        According to the DoD Issuance Style Guide:
            "It [the glossary] is always the second to last section in an
            issuance, followed only by the References section."
        """
        glossary_start = next(
            (
                i
                for i in range(self.num_of_sections)
                if self._get_subsection(i).startswith("GLOSSARY")
            ),
            None,
        )

        if glossary_start:
            ref_start = next(
                (
                    i
                    for i in range(glossary_start + 1, self.num_of_sections)
                    if self._get_subsection(i).startswith("REFERENCES")
                    or self._get_subsection(i).startswith("ENCLOSURE")
                ),
                None,
            )
            if ref_start:
                self.combine_sections(glossary_start, ref_start - 1)
                ref_start = glossary_start + 1
                ref_end = next(
                    (
                        i
                        for i in range(ref_start, self.num_of_sections)
                        if self._get_subsection(i).startswith("ENCLOSURE")
                    ),
                    self.num_of_sections,
                )
                self.combine_sections(ref_start, ref_end - 1)
            else:
                self.combine_sections(glossary_start, self.num_of_sections - 1)

    def _remove_repeated_section_titles(self):
        """Updates self._sections so that section titles only appear once, at 
        the beginning of each section.
        
        This is necessary because section titles are repeated when a section 
        spans more thn 1 page.
        """
        for i in range(self.num_of_sections):
            first_subsection = self._get_subsection(i)
            is_first_toc = is_toc(first_subsection)

            if not is_first_toc and starts_with_glossary(first_subsection):
                self._sections[i][1:] = [
                    subsection
                    for subsection in self._sections[i][1:]
                    if not starts_with_glossary(subsection.strip())
                ]
                continue
            
            enclosure_num = match_enclosure_num(first_subsection)
            if enclosure_num:
                self._sections[i][1:] = [
                    subsection
                    for subsection in self._sections[i][1:]
                    if not match_enclosure_num(subsection.strip(), enclosure_num)
                ]

            self._sections[i][1:] = [
                subsection
                for subsection in self._sections[i][1:]
                if subsection.strip().lower() != first_subsection.lower()
            ]

    def _get_subsection(
        self, section_index, subsection_index: int = 0, strip_text: bool = True
    ) -> str:
        subsection = self._sections[section_index][subsection_index]
        if strip_text:
            subsection = subsection.strip()
        return subsection

    def _remove_pagebreak(self, text: str) -> str:
        """Remove pagebreak noise from text.

        Args:
            text (str): Should have no leading whitespaces.

        Returns:
            text (str): The cleaned text.

        Example:
            `text` = "DoDD 4124.01E December 12, 1994 ENCLOSURE 1 RESPONSIBILITIES"
            `pagebreak_text` = "DoDD 4124.01"
            returns: "ENCLOSURE 1 RESPONSIBILITIES"
        """
        pagebreak_match = match(
            rf"{self._pagebreak_text}(?:[-,]? ?V(?:olume|OLUME)? ?[0-9]{{1,3}})?,?",  # optional volume number
            text
        )

        if self._pagebreak_text and pagebreak_match:
            text = text[pagebreak_match.end():].lstrip()
            date_span = find_pagebreak_date(text)
            if date_span is not None and date_span[0] < 5:
                text = text[date_span[1] :].strip()

        return text

    def _should_skip(self, text: str) -> bool:
        if not text:
            return True

        if text.isspace():
            return True

        # Usually a page number
        if text.isdigit():
            return True

        is_text_short = len(text) < 40

        # Pagebreak in text and text is short -> probably a header or footer.
        if (
            len(self._pagebreak_text) > 0
            and is_text_short
            and match(self._pagebreak_text, text, flags=IGNORECASE)
        ):
            return True

        # Header/ footer
        if is_text_short and match(r"change [0-9]", text, flags=IGNORECASE):
            return True

        # Page number/ footer
        if search(r"[\t][0-9]{1,3}$", text):
            return True

        # Page number/ footer of an Enclosure
        if fullmatch(
            r"[0-9]{1,3}(?:[\t]+|\s{4,})(?:ENCLOSURE|ATTACHMENT|GLOSSARY)(?:\s+[0-9]{1,2})?",
            text,
            flags=IGNORECASE,
        ):
            return True

        return False
