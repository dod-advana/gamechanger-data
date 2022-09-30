from re import match, search, fullmatch, VERBOSE, IGNORECASE
from typing import List
from docx.text.paragraph import Paragraph
from common.document_parser.lib.section_parse.utils import is_alpha_list_item
from .utils import (
    get_subsection,
    is_glossary_continuation,
    match_enclosure_num,
    is_list_child,
    is_toc,
    get_subsection,
    is_first_line_indented,
    is_sentence_continuation,
    ends_with_continued,
    starts_with_part,
    ends_with_colon,
    is_next_num_list_item,
    is_bold,
    starts_with_bullet,
    is_attachment_start,
)


def is_enclosure_continuation(text: str, prev_section: List[str]) -> bool:
    """Determine if `prev_section` is an Enclosure (or Attachment) section
    title and if `text` is part of that title.

    Returns True if:
        - `prev_section` contains only 1 item.
        - The 1 item in `prev_section` is the start of an Enclosure.
        - `text` is all uppercase and does not start with a digit, or the 1
           item in `prev_section` only contains an Enclosure number.

    This is used to combine parts of an Enclosure section title.

    Example:
        text = "ENCLOSURE 4 "
        prev_section = ["RESPONSIBILITIES"]
        --> Returns True

        text = "ATTACHMENT"
        prev_section = ["REFERENCES"]
        --> Returns True

        text = "ENCLOSURE 5 is the best."
        prev_section = ["It states that..."]
        --> Returns False

    Args:
        text (str)
        prev_section (list of str): The section before `text`.

    Returns:
        bool: True if `text` is a continuation of `prev_section`, False otherwise.
    """
    if len(prev_section) == 1 and not match(
        "GLOSSARY", text, flags=IGNORECASE
    ):
        if (
            is_attachment_start(get_subsection(prev_section))
            and text.isupper()
        ):
            return True

        prev_section = prev_section[0].strip()
        prev_enclosure = match_enclosure_num(prev_section, return_type="match")

        if prev_enclosure:
            curr_enclosure = match_enclosure_num(text)
            # If `text` references an Enclosure number that is not the same
            # Enclosure number referenced in `prev_section`, return False.
            if (
                curr_enclosure is not None
                and curr_enclosure != prev_enclosure.groups()[0]
            ):
                return False
            if text.isupper() and not text[0].isdigit():
                return True

    return False


def should_skip(text: str, fn: str) -> bool:
    """Returns whether or not the text should be skipped when adding to
    document sections.

    This is used to eliminate noise.

    Args:
        text (str): Determine if this text should be added to sections or
            skipped. Important: leading and trailing whitespaces should be
            stripped.
        fn (Union[str, PathLike]): File name (without extension) of the
            document. Should be of the format: doc_type + " " + doc_num

    Returns:
        bool: True if the text should not be part of document sections, False
            otherwise.
    """
    if (
        # Usually a page number
        text.isdigit()
        # File name in text and text is short -> probably a header or footer
        or (
            len(fn) > 0
            and (match(fn, text, flags=IGNORECASE) and len(text) < 40)
        )
        # Another header/ footer presentation
        or (match(r"change [0-9]", text, flags=IGNORECASE) and len(text) < 40)
        # Page number/ footer
        or search(r"[\t][0-9]{1,3}$", text)
        # Page number/ footer of an Enclosure
        or fullmatch(
            r"[0-9]{1,3}\s?[\t](?:ENCLOSURE|ATTACHMENT|GLOSSARY)(?:\s[0-9]{1,2})?",
            text,
            flags=IGNORECASE,
        )  # Page num of enclosure
    ):
        return True

    return False


def is_known_section_start(text: str, par: Paragraph) -> bool:
    """Returns whether or not the text is a known section starting point.

    Args:
        text (str): Determine if this text is the start of a section.

    Returns:
        bool: True if the text is a known section starting point, False
            otherwise.
    """
    # Don't split up the table of contents.
    if is_toc(text):
        return False

    if text[:1].isupper():
        m = match(
            r"""
                (?:[0-9]{1,2}[\.\)\s]?\s)?      # Optional group: 1-2 digits, optional period/ closing parenthesis/ whitespace, whitespace.
                (
                    Ref(?:erence)?s?            # "Ref" or "Refs" or "Reference" or "References"
                    |Sub(?:j(?:ect)?)?          # "Sub" or "Subj" or "Subject"
                    |Purpose
                    |Applicability
                    |Policy
                    |Responsibilities     
                    |Relationships
                    |Authorities
                    |Releasability
                    |Summary\sof\sChange
                    |Effective\sDate
                    |(?:E\.?[0-9]{1,2}\.?\s)    # Enclosure number: E, optional period, 1-2 digits, optional period, space.
                    |(?:Enclosure\s[0-9]{1,2})  
                    |Reissuance
                    |Procedures
                    |Table\sOf\sContents
                )
                ([:\.])?
            """,
            text,
            flags=VERBOSE | IGNORECASE,
        )
        if m:
            groups = m.groups()
            # Must be all uppercase, end with colon/ period, or be bold to be
            # a section start
            if groups[0].isupper() or groups[1] is not None or is_bold(par):
                return True

    # Separate match for "Glossary" because it does not need to be followed by
    # a colon or period if not uppercase.
    if match(r"Glossary", text, flags=IGNORECASE):
        return True

    # Note: Don't use IGNORECASE flag here because "Section" is commonly referred to
    # within section bodies.
    # Starts with "SECTION <number>" and does not end with tab & 1-3 digits.
    # (Tab & 1-3 digits usually indicates the end of a page.)
    if match(r"SECTION\s[0-9]{1,2}", text) and not search(
        r"[\t][0-9]{1,3}$", text
    ):
        return True

    return False


def is_child(par: Paragraph, prev_section: List[str], space_mode: int) -> bool:
    """Determine if `par` is a child/ subsection of `prev_section`.

    Args:
        par (Paragraph): Paragraph of a docx document.
        prev_section (list of str): The section directly before `par` in the
            document.
        space_mode (int): Mode value of space before a block. See
            DocxParser.calculate_space_mode().

    Returns:
        bool: True if `par` is a child/ subsection of `prev_section`, False
            otherwise.
    """
    text = par.text
    text_stripped = text.strip()
    last_sub = get_subsection(prev_section, -1, False)
    last_sub_stripped = " ".join(last_sub.split()).strip()
    first_sub = " ".join(get_subsection(prev_section).split())

    # Check if the paragraph is part of a Table of Contents.
    if is_toc(text):
        if is_toc(first_sub):
            return True
        else:
            return False

    if (
        is_first_line_indented(par)
        or text_stripped.startswith("Table")
        or starts_with_bullet(text_stripped)
        or is_sentence_continuation(text, last_sub)
        or par.paragraph_format.space_before < space_mode
        or is_alpha_list_item(text_stripped)
        # If the previous section only has 1 subsection and is all uppercase,
        # it's likely a section header.
        or (len(prev_section) == 1 and first_sub.isupper())
        or ends_with_continued(last_sub_stripped)
        or starts_with_part(text_stripped)
        or is_glossary_continuation(text_stripped)
        or ends_with_colon(last_sub_stripped)
    ):
        return True

    prev_enclosure = match_enclosure_num(first_sub)
    if prev_enclosure:
        if match_enclosure_num(text_stripped, prev_enclosure, "bool"):
            return True
        # Typically, numbered list are separate sections so we don't combine
        # them. But, we do want to combine numerical lists within Enclosures.
        if text_stripped.startswith("1.") or is_next_num_list_item(
            text_stripped, prev_section
        ):
            return True

    if is_list_child(text_stripped, prev_section):
        return True

    return False


def is_same_section_num(text: str, section: List[str]) -> bool:
    """Determine whether `text` has the same section number as `section`.

    Args:
        text (str)
        section (list of str)

    Returns:
        bool: True if `text` has the same section number as `section`, False
            otherwise.
    """
    # If `text` and/ or `section` are part of the Table of Contents, return False.
    for s in [text, " ".join(section)]:
        if is_toc(s):
            return False

    first_subsection = " ".join(get_subsection(section).split())
    text = text.strip()

    section_num = match(
        r"""
            section\s([0-9]{1,2})             # "section", space, 1-2 digits
            |([A-Z]{0,2}[0-9]{1,2})\.[\s0-9]  # OR: 0-2 letters, 1-2 digits, period, space or digit
        """,
        first_subsection,
        flags=VERBOSE | IGNORECASE,
    )

    if section_num:
        section_num = next(
            num for num in section_num.groups() if num is not None
        )
        if match(
            rf"""
                {section_num}\.[0-9]{{1,2}}     # The section number, period, 1-2 digits.
                |section\s{section_num}\b       # OR: "section", space, 1-2 digits, word boundary.
            """,
            text,
            flags=VERBOSE | IGNORECASE,
        ):
            return True

    return False
