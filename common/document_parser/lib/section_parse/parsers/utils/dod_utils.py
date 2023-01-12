"""Utilities for DoDParser."""

from re import compile, search, match, IGNORECASE, VERBOSE, Match
from typing import Union, Tuple, List, Callable
from .shared_utils import MONTH_LIST


PAGEBREAK_DATE_PATTERN = compile(
    r"(?:" + r"|".join(MONTH_LIST) + r") [0-9]{1,2}[,\.]? (?:19[0-9]{2}|2[0-9]{3})"
)


def find_pagebreak_date(text: str) -> Union[Tuple[int, int], None]:
    """Find the start and end of a pagebreak date within the text.

    Most documents have one date of the following format in each pagebreak:
        <month> <1-2 digit day> <optional comma> <4-digit year>
        Example: `March 12, 2004`.

    Args:
        text (str)

    Returns:
        Union[Tuple[int, int], None]: If a date is found, returns a Tuple of
            ints (date start index, date end index). Otherwise, returns None.
    """
    date_match = search(PAGEBREAK_DATE_PATTERN, text)
    if date_match:
        return (date_match.start(), date_match.end())
    else:
        return None


def match_alpha_list_item(
    text: str,
) -> Union[Tuple[str, Callable], Tuple[None, None]]:
    """Match an alphabetical (lowercase only) list item.

    Args:
        text (str)

    Returns:
        Union[Tuple[str, Callable], Tuple[None, None]]:  If an alphabetical
            list item is found, the first item of the tuple will be the letter
            from that item and the second item will be the function that found
            the match. Otherwise, the both items will be None.
    """
    letter = match_alpha_dot(text)
    if letter:
        return (letter, match_alpha_dot)

    letter = match_alpha_single_paren(text)
    if letter:
        return (letter, match_alpha_single_paren)

    letter = match_alpha_double_parens(text)
    if letter:
        return (letter, match_alpha_double_parens)

    return (None, None)


def match_alpha_dot(text: str) -> Union[str, None]:
    """Helper for match_alpha_list_item()."""
    m = match(r"([a-z])\. ", text)
    return m.groups()[0] if m else None


def match_alpha_single_paren(text: str) -> Union[str, None]:
    """Helper for match_alpha_list_item()."""
    m = match(r"([a-z])\) ", text)
    return m.groups()[0] if m else None


def match_alpha_double_parens(text: str) -> Union[str, None]:
    """Helper for match_alpha_list_item()."""
    m = match(r"\(([a-z])\) ", text)
    return m.groups()[0] if m else None


def is_sentence_continuation(text: str, prev_text: str) -> bool:
    """Check if `text` is a continuation of the sentence `prev_text`.

    Note: do NOT strip leading/ trailing whitespace from the params.
    """
    # prev_text: ends with lowercase letter, optional single space, and 
    #   anything other than a period or letter. 
    # text: starts with a lowercase letter.
    # Example:
    #   prev_text = "to execute DSCA plans as directed."
    #   text = "Ensure the appropriate personnel are trained "
    #   --> "Ensure the appropriate personnel are trained to execute DSCA plans as directed."
    if search(r"[a-z] ?[^\.] $", prev_text) and match(r"[a-z]", text):
        return True

    # prev_text: ends with either:
    #       - letter, hyphen
    #       - comma, any 2 characters, 1 or more spaces
    # text: starts with any letter
    # Example:
    #   prev_text = "ASSISTANT SECRETARY OF DEFENSE FOR SPECIAL OPERATIONS AND LOW-"
    #   text = "INTENSITY CONFLICT"
    #   --> "ASSISTANT SECRETARY OF DEFENSE FOR SPECIAL OPERATIONS AND LOW-INTENSITY CONFLICT"
    elif search(r"(?:[a-zA-Z]\-|,.{0,2}\s+)$", prev_text) and match(
        r"[a-zA-Z]", text
    ):
        return True

    # prev_text: ends with "under", "in", "with", or "to"
    # text: starts with "Section", single space, number
    # Example:
    #   prev_text = "This provision is stated under "
    #   text = "Section 8 of Title 10. "
    #   --> "This provision is stated under Section 8 of Title 10."
    elif search(r"(?:under|in|with|to) +$", prev_text) and match(
        r"Section [0-9]", text
    ):
        return True

    # prev_text: ends with "in", 1 or more spaces, "the", 1 or more spaces
    # text: starts with "Glossary"
    # Example:
    #   prev_text = "Definitions can be found in the "
    #   text = "Glossary."
    #   --> "Definitions can be found in the Glossary."
    elif search(r"in +the +$", prev_text) and match("Glossary", text):
        return True

    # Edge case: Deputy Secretary of Defense
    elif prev_text.endswith("Deputy ") and text.startswith("Secretary of Defense"):
        return True

    return False


def is_toc(text: str) -> bool:
    """Check if the text is part of a document's Table of Contents section."""
    return (
        search(r"table\sof\scontents|\.{5,}", text, flags=IGNORECASE)
        is not None
    )


def is_known_section_start(text: str) -> bool:
    """Returns whether or not the text is a known section starting point.

    Args:
        text (str): Determine if this text is the start of a section.

    Returns:
        bool: True if the text is a known section starting point, False
            otherwise.
    """
    # Check if first letter is uppercase.
    first_letter_match = search(r"[a-zA-Z]", text)
    if first_letter_match and first_letter_match.group().isupper():
        m = match(
            r"""
                (?:[0-9]{1,2}[\.\)\s]?\s+)?      # Optional group: 1-2 digits, optional period/ closing parenthesis/ whitespace, whitespace.
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
            if groups[0].isupper() or groups[1] is not None:
                return True

        # Separate match for "Glossary" and "Enclosures" because they don't need
        #  to be followed by a colon or period if they're not uppercase.
        if match(r"(?:Glossary|Enclosures)", text, flags=IGNORECASE):
            return True

        if match(r"Appendix +[A-Z0-9]", text, flags=IGNORECASE):
            return True

    return False


def match_enclosure_num(
    text: str, num: Union[int, str, None] = None
) -> Union[str, None]:
    """Find an Enclosure number within a string.

    Attempts to match at the start of `text`. If no match is found, returns
    None.

    Args:
        text (str): Should not have any leading whitespace.
        num (int or None, optional): To match any 1-2 digit Enclosure number,
            use None. Otherwise, pass the enclosure number to match.
    Returns:
        str or None: If an Enclosure number is found, returns it as a str.
            Otherwise, returns None.
    """
    partial_pattern = r"E\.?"
    if num is None:
        partial_pattern += r"([0-9]{1,2})"
    else:
        partial_pattern += rf"({str(num)})"
    partial_pattern += r"[\s\.]"

    num_match = match(partial_pattern, text)
    if num_match:
        return num_match.groups()[0]

    full_pattern = r"E(?:nclosure|NCLOSURE)\s+"
    if num is None:
        full_pattern += r"([0-9]{1,2})"
    else:
        full_pattern += rf"({str(num)})"

    num_match = match(full_pattern, text)

    return num_match.groups()[0] if num_match else None


def match_section_num(
    text: str, num: Union[int, None] = None
) -> Union[str, None]:
    """Match a section number in the text.

    Args:
        text (str): Text to look for a section number in. Should have no
            leading whitespace.
        num (int or None, optional): If int, looks for this section number.
            If None, looks for any section number (with 0-2 letters and
            1-2  digits). Defaults to None.

    Returns:
        str or None: If a section number is found, returns it as a str. If no
            match is found, returns None.
    """
    if is_toc(text):
        return None

    if num is None:
        num = match(
            r"""
                section\s([0-9]{1,2})         
                |([A-Z]{0,2}\.?[0-9]{1,2})\.\s   
                |([0-9]{1,2})\.[0-9](?:(?!\.[a-zA-Z]))
            """,
            text,
            flags=VERBOSE | IGNORECASE,
        )
    else:
        num = match(
            rf"section\s({num})|({num})\.[\s0-9]", text, flags=IGNORECASE
        )

    if num is not None:
        return next((n for n in num.groups() if n is not None), None)

    return None


def match_ref_start(text: str) -> Union[Match, None]:
    """Match the start of a References section."""
    return match(
        rf"""
            (?:
                R(?:ef|EF)(?:\:|,\s+continued)
                |R(?:eferences|EFERENCES)(?:\:|\s|,\s+continued)
            )
        """,
        text,
        flags=VERBOSE,
    )


def next_section_num(text: str) -> str:
    """Given a section number, determine the number of the section that should
    follow it.

    Args:
        text (str): The current section number.

    Returns:
        str: The next section number.
    """
    alpha_chars = "".join([char for char in text if char.isalpha()])
    digit_chars = "".join([char for char in text if char.isdigit()])

    if not digit_chars:
        return ""

    return alpha_chars + str(int(digit_chars) + 1)


def starts_with_glossary(text: str) -> bool:
    """Check if the text starts with "Glossary" or "GLOSSARY".

    Note: strip leading whitespace from `text`.
    """
    return match(r"G(?:LOSSARY|lossary)", text) is not None


def get_subsection_of_section_1(
    section_1: List[str], subsection_name: str
) -> List[str]:
    """Get a subsection from Section 1 of a document.

    Sometimes, sections such as "Applicability" and "Policy" are subsections of
    Section 1 instead of being standalone sections. This function is used to
    extract those subsections from Section 1.

    Args:
        section_1 (List[str]): Texts from Section 1 of a document.
        subsection_name (str): The name of the subsection to get.

    Returns:
        List[str]
    """
    start_index = None
    end_index = None

    for i in range(len(section_1)):
        text = section_1[i].strip()
        if start_index is None:
            if is_subsection_start_for_section_1(text, subsection_name):
                start_index = i
        elif end_index is None:
            if is_subsection_start_for_section_1(text, ""):
                end_index = i
                break
        else:
            break

    if start_index is None:
        return []

    end_index = end_index if end_index is not None else len(section_1)

    return ["\n".join(section_1[start_index:end_index])]


def is_subsection_start_for_section_1(text: str, subsection_name: str) -> bool:
    """Check if `text` is the start of a subsection within a document's Section 1.

    Args:
        text (str): The text to check. Should have leading whitespaces removed.
        subsection_name (str): If "", will check for a generic subsection start.
            Otherwise, will look for this specific subsection name.

    Returns:
        bool
    """
    # "1", period, 1-2 digits, optional period, 1 or more whitespaces
    name_pattern = rf"(?:1\.[0-9]{{1,2}}\.?\s+)"

    if subsection_name == "":
        if match(rf"{name_pattern}", text):
            return True
        known_subsection_names = [
            x
            for x in ["Applicability", "Policy", "Information Collections"]
            if x.lower() != subsection_name.lower()
        ]
        for name in known_subsection_names:
            if text.lower().startswith(name.lower()) and text[:1].isupper():
                return True
    else:
        # If no subsection name is specified, make the number pattern optional.
        name_pattern += r"?"

        for word in subsection_name.split(" "):
            name_pattern += rf"{word[:1].upper()}(?:{word[1:].lower()}|{word[1:].upper()})\s+"
        name_pattern = name_pattern.rstrip(r"\s+")
        name_pattern += r"\b"
        return match(rf"{name_pattern}", text) is not None

    return False
