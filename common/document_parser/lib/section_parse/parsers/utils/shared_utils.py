from calendar import month_name
from re import sub, search, RegexFlag, Match, VERBOSE
from typing import List, Union


def make_pattern_for_uppercase_or_titlecase(s: str) -> str:
    """Returns a string that can be used in a regex pattern to match the `s`
    in uppercase titlecase.

    Example: input = "january", output = r"J(?:ANUARY|anuary)"
    """
    # Unexpected matches can happen downstream if the input string is empty.
    # Be careful!
    return rf"{s[:1].upper()}(?:{s[1:].upper()}|{s[1:].lower()})"


# [r"J(?:ANUARY|anuary)", r"F(?:EBRUARY|ebruary)", ...]
# Used to match a month that is uppercase or titlecase.
MONTH_LIST = [
    make_pattern_for_uppercase_or_titlecase(m) for m in month_name[1:]
]

# [r"J(?:AN|an)", r"F(?:EB|eb)", ...]
# Used to match a month abbreviation that is uppercase or titlecase.
MONTH_ABBREVIATIONS_LIST = [
    make_pattern_for_uppercase_or_titlecase(month_abbrev)
    for month_abbrev in [
        "jan",
        "feb",
        "mar",
        "apr",
        "jun",
        "jul",
        "aug",
        "sep",
        "sept",
        "oct",
        "nov",
        "dec",
    ]
]

# Used to match a month in the form:
#   <1-2 digit day> <month name or abbreviation> <4-digit year>
# Example: '12 DECEMBER 2014', '5 Aug 1998'
DD_MONTHNAME_YYYY = rf"""
        (?:[0-2]?[0-9]|3[01])                                   # 1-2 digit day
        [ ]                                                     # Single space
        (?:{'|'.join(MONTH_LIST + MONTH_ABBREVIATIONS_LIST)})   # Full or abbreviated month name
        [ ]                                                     # Single space
        [1-2]                                                   # "1" or "2" (year)
        [0-9]{{3}}                                              # 3 digits (year)
"""


# UPPERCASE or TitleCase "enclosure" used in regex patterns.
CAPITAL_ENCLOSURE = r"E(?:nclosure|NCLOSURE)"


def next_letter(char: str) -> str:
    """Get the next letter in the alphabet.

    Args:
        char (str): Return the letter after this one.

    Raises:
        ValueError: If the input is not a single letter.

    Returns:
        str
    """
    if len(char) != 1 or not char.isalpha():
        raise ValueError(
            f"input for `next_letter()` must be a single letter but was: `{char}`."
        )
    if char.isupper():
        # ord("A") = 65
        return chr((ord(char) - 64) % 26 + 65)
    else:
        # ord("a") = 97
        return chr((ord(char) - 96) % 26 + 97)


def remove_pagebreaks(
    text: str, pagebreak: str, regex_flags: List[RegexFlag] = []
) -> str:
    """Remove a pagebreak from the given text.

    NOTE: The VERBOSE flag will always be applied. Make sure the `pagebreak`
    pattern accounts for this (for example, change '\n' -> '[\n]', ' ' -> '[ ]',
    '\t' -> '[\t]', etc).

    Args:
        text (str): Text to remove pagebreaks from.
        pagebreak (str): Pattern of the pagebreak text
        regex_flags (List[RegexFlag], optional): Defaults to [].

    Returns:
        str
    """
    if VERBOSE not in regex_flags:
        regex_flags.append(VERBOSE)

    flags = 0
    for flag in regex_flags:
        flags |= flag

    return sub(
        rf"""
            (?:^|[\n])          # Either match at the start of the text, or match a newline.
            [ ]*                # Any number (including 0) of spaces 
            {pagebreak}
            [ ]*                # Any number (including 0) of spaces
            (?:(?=[\n])|$)      # Either match at the end of the text, or match a newline.
        """,
        "",
        text,
        flags=flags,
    )


def find_first_occurrence(text: str, patterns) -> Union[Match, None]:
    """Find the first occurrence of a pattern match (lowest start index) within 
    the text.

    Note: If 2 matches have the same start index, the returned match is the one 
    whose pattern is first in the `patterns` param.

    Args:
        text (str): Text to search in.
        patterns (str or re.Pattern): Patterns to search for in the text.

    Returns:
        Union[Match, None]: If a match(es) found, returns the match with the 
            lowest start index. If no match is found, returns None.
    """
    first_match = None

    for pattern in patterns:
        match_ = search(pattern, text)
        if match_:
            if first_match is None or match_.start() < first_match.start():
                first_match = match_

    return first_match


def make_linebreak_pattern(text):
    return rf"\n\s*{text}\s*\n"
