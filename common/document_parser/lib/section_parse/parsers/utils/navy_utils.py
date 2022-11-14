from re import compile, search, Match, RegexFlag, IGNORECASE, VERBOSE
from typing import Union, List
from .shared_utils import next_letter

# Pattern to match the start of an Appendix section title.
APPENDIX_TITLE_PATTERN = compile(
    rf"""
        \s*[\n]                 # Any number of whitespaces, then a newline
        (?:                     # Start of an optional, non-capture group
            [A-Z]                   # 1 uppercase letter
            [ ]?                    # Optional space
            -                       # Hyphen
            [ ]?                    # Optional space
            [1-9][0-9]?             # 1 digit in 1-9, then optional digit in 0-9
            \s*                     # Any number of whitespace
        )?
        A(?:ppendix|PPENDIX)    # "Appendix" or "APPENDIX"
        [ ]                     # 1 space
        [A-Z]                   # 1 uppercase letter
        \s*[\n]                 # Any number of whitespaces, then a newline
    """,
    flags=VERBOSE,
)


def get_letter_dot_section(
    text: str, section_name: str, regex_flags: List[RegexFlag] = [IGNORECASE]
) -> str:
    """Get a section, that is part of an alphabetical list and has the given
    section name, from the text.

    Args:
        text (str): Text to extract the section from.
        section_name (str): Name of the section to extract.
        regex_flags (List[RegexFlag], optional): Regex flags to use in search.
            Defaults to [IGNORECASE].

    Returns:
        str
    """
    # Note: only gets the first section that is a match.
    default = ""

    if not text:
        return default

    flags = 0

    for flag in regex_flags:
        flags |= flag

    start_match = search(
        rf"\n\s*([a-zA-Z])\.\s*{section_name}", text, flags=flags
    )

    if not start_match:
        return default

    letter = start_match.groups()[0]
    start_index = start_match.start()
    crop_start_index = start_match.end()
    start_match_len = crop_start_index - start_index
    cropped_text = text[crop_start_index:]

    end_patterns = [
        rf"\n\s*({next_letter(letter)})\.\s*",
        r"\n\s*[0-9]+\.\s",
        r"\n\s*\n",
        "\n",
    ]
    end_match = None
    for pattern in end_patterns:
        end_match = search(pattern, cropped_text)
        if end_match:
            break
    if end_match:
        return text[
            start_index : start_index + start_match_len + end_match.start()
        ]

    return text[start_index:]


def match_number_hyphenated_section(
    text: str, first_num: str = "[0-9]+", second_num: str = "[0-9]+"
) -> Union[Match, None]:
    """Match the start of a section that is formatted with hyphenated numbers
    and has the given section number.

    Ex: "\n1-2. PURPOSE\nThis publication..."

    Args:
        text (str): Text to extract a section from.
        first_num (str, optional): Number to the left of the hyphen. Defaults
            to "[0-9]+".
        second_num (str, optional): Number to the right of the hyphen. Defaults
            to "[0-9]+".

    Returns:
        Union[Match, None]: If a match is found, returns it as a Match object.
            Otherwise, returns None.
    """
    return search(rf"\n{first_num}-{second_num}\s*\.?", text)


def match_number_dot_section(
    text: str, num: str = "[0-9]+"
) -> Union[Match, None]:
    return search(rf"\n{num}\s*\.", text)


def match_first_appendix_title(text: str) -> Union[Match, None]:
    return search(APPENDIX_TITLE_PATTERN, text)
