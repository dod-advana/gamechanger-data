"""Utility functions for section parsing.

These functions are meant to be small units that make the Sections class easier 
to read and test.
"""

from re import search, match, VERBOSE, IGNORECASE, Match
from docx.text.paragraph import Paragraph
from roman import fromRoman
from typing import Union, List


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
                |([0-9]{1,2})\.[0-9]
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


def match_roman_numerals(text: str) -> Union[int, None]:
    """Get roman numerals at the start of `text` as an integer.

    Looks for 1-5 roman numerals at the start of `text`. If a match is found,
    attempts to convert the roman numeral to an integer. If the attempt fails
    or no match was found, returns None.
    """
    m = match(r"([IVXLCDM]){1,5}\b", text)
    if m:
        try:
            m = fromRoman(m.group())
        except:
            m = None

    return m


def match_enclosure_num(
    text: str, num: Union[int, None] = None, return_type: str = "str"
) -> Union[str, None, Match, bool]:
    """Get an Enclosure number from `text`.

    Attempts to match at the start of `text`. If no match is found, returns
    None.

    Note: strip leading whitespace from `text`.

    Args:
        text (str)
        num (int or None, optional): To match a specific Enclosure number, pass
            an int. To match any Enclosure number (1-2 digits), pass None.
            Defaults to None.
        return_type ("str", "match", or "bool", optional): The type to return.
            Use "str" to return the Enclosure number match as a str (if no
            match is found, returns None). Use "match" to return re.Match.
            Use "bool" to return True if a match is found and False otherwise.
            Defaults to "str".
    Returns:
        str or None or re.Match or bool: Depends on `return_type` arg.

    Raises:
        ValueError: If invalid value passed for `return_type` arg.
    """
    pattern = rf"""
             (?:
                E?
                [0-9]{{1,2}}
                \.?
                \s+
            )?
            E(?:NCLOSURE|nclosure)
            \s
    """
    if num is None:
        pattern += r"([0-9]{1,2})"
    else:
        pattern += rf"({num})"

    num_match = match(pattern, text, flags=VERBOSE)

    if return_type == "str":
        return num_match.groups()[0] if num_match else None
    elif return_type == "match":
        return num_match
    elif return_type == "bool":
        return num_match is not None
    else:
        raise ValueError(
            f"Invalid arg '{return_type}'. `return_type` must be 'str' or 'match' or 'bool'. "
        )


def match_num_list_item(text: str) -> Union[str, None]:
    """If the text starts with number list formatting, returns the number as a
    string. Otherwise, returns None. Supports up to 2 digits.
    """
    # Ex: "1.", "2)"
    num = match(r"\(?([0-9]{1,2})[\.\)]", text)

    return num.groups()[0] if num else None


def match_num_dot(text: str) -> Union[str, None]:
    """If `text` starts with 1-2 digits and a dot, returns the digits.
    Otherwise, returns None.
    """
    num = match(r"([0-9]{1,2})\.", text)
    return num.groups()[0] if num else None


def match_num_parentheses(text: str) -> Union[str, None]:
    """If `text` starts with (optional opening parenthesis,) 1-2 digits, closing
    parenthesis, returns the digits. Otherwise, returns None.
    """
    num = match(r"\(?([0-9]{1,2})\)", text)
    return num.groups()[0] if num else None


def is_bold(par: Paragraph) -> bool:
    """Check if all text in the paragraph is bold."""
    return all([run.bold for run in par.runs]) and len(par.runs) > 0


def is_first_line_indented(par: Paragraph) -> bool:
    """Check if the first line of the paragraph is indented."""
    return (
        par.paragraph_format.first_line_indent
        and par.paragraph_format.first_line_indent > 0
    ) or par.text.startswith("\t")


def is_sentence_continuation(text: str, prev_text: str) -> bool:
    """Check if `text` is a continuation of the sentence `prev_text`.

    Note: do NOT strip leading/ trailing whitespace from the params.
    """
    result = (search(r"[^\.] $", prev_text) and match(r"[a-z]", text) is not None)
    if result is None:
        return False
    return result


def is_alpha_list_item(text: str) -> bool:
    """Check if `text` is an item of an alphabetical list."""
    # Ex: "a. ", "b) ", "(c) "
    return (
        match(r"[a-z]{1,2}\.\s|\(?[a-z]{1,2}\)\s", text, flags=IGNORECASE)
        is not None
    )


def is_toc(text: str) -> bool:
    """Check if the text is part of a document's Table of Contents section."""
    return (
        search(r"table\sof\scontents|\.{5,}", text, flags=IGNORECASE)
        is not None
    )


def is_glossary_continuation(text: str) -> bool:
    """Check if the text is a continuation of a Glossary.

    Note: strip leading whitespace from `text`.
    """
    # Ex: "2 Glossary", "G.3"
    return (
        match(r"[0-9]{1,3}\sG(?:LOSSARY|lossary)|G\.[1-9]{1,2}\.?\s", text)
        is not None
    )


def is_next_num_list_item(text: str, prev_section: List[str]) -> bool:
    """Check if `text` is the next item in a numbered list from `prev_section`.

    Note: strip leading whitespace from `text`.
    """
    last_num = None
    num_dot = match_num_dot(text)
    if num_dot:
        for subsection in reversed(prev_section):
            last_num = match_num_dot(subsection.strip())
            if last_num:
                break

        if last_num is not None:
            return int(num_dot) == int(last_num) + 1

        return False

    num_paren = match_num_parentheses(text)
    if num_paren:
        for subsection in reversed(prev_section):
            last_num = match_num_parentheses(subsection.strip())
            if last_num:
                break

        if last_num is not None:
            return int(num_paren) == int(last_num) + 1

        return False

    return False


def is_list_child(text: str, prev_section: List[str]) -> bool:
    """Check if `text` is part of a list in `prev_section`.

    Checks for the following list types:
        - Roman numerals
        - {number or letter}.{number}
        - Enclosure subpart (Ex: "E1.2")

    Note: strip leading whitespace from `text`
    """
    # Check if the text is a continuation of a roman numeral list.
    curr_roman = match_roman_numerals(text)
    if curr_roman:
        for sub in reversed(prev_section):
            prev_roman = match_roman_numerals(sub)
            if prev_roman is not None and curr_roman == prev_roman + 1:
                return True

    # Check if the text is a continuation of a {number or letter}.{number} list.
    curr_nums = match(r"([0-9A-Z]{1,2})\.([0-9]{1,2})\b", text)
    if curr_nums:
        curr_nums = curr_nums.groups()
        for sub in reversed(prev_section):
            prev_nums = match(r"([0-9]{1,2})\.([0-9]{1,2})\b", sub)
            if prev_nums:
                prev_nums = prev_nums.groups()
                if len(prev_nums) == 2 and len(curr_nums) == 2:
                    if prev_nums[0] == curr_nums[0]:
                        return True

    # Check if the text is a continuation of an enclosure.
    curr_encl = match(r"E([0-9]){1,2}\.[\s0-9]", text)
    if curr_encl:
        curr_encl = curr_encl.groups()[0]
        for sub in reversed(prev_section):
            prev_encl = match(r"E([0-9]{1,2})\.[\s0-9]", sub)
            if prev_encl and prev_encl.groups()[0] == curr_encl:
                return True

    return False


def is_space(text: str) -> bool:
    """Check if the text is empty or contains only whitespace."""
    return not text or text.isspace()


def next_section_num(text: str) -> str:
    alpha_chars = "".join([char for char in text if char.isalpha()])
    digit_chars = "".join([char for char in text if char.isdigit()])

    if not digit_chars:
        return ""

    return alpha_chars + str(int(digit_chars) + 1)


def starts_with_part(text: str) -> bool:
    """Check if the text starts with a section part.

    Note: strip leading whitespace from `text`.

    Example: "Part 2 ...", "Part A ...", "Part 4B ..."
    """
    return match(r"Part\s[A-Z0-9]{1,3}", text, flags=IGNORECASE) is not None


def ends_with_continued(text: str) -> bool:
    """Check if the text ends with "continued" or "Continued"."""
    return search(r"\b[Cc]ontinued$", text) is not None


def ends_with_colon(text: str) -> bool:
    """Check if the text ends with a colon (and optional whitespace)."""
    return search(":\s?$", text) is not None


def get_subsection(
    section: List[str], ind: int = 0, strip: bool = True
) -> str:
    """Get a subsection from `section`.

    If no item exists at `ind`, returns an empty string.

    Args:
        section (List[str])
        ind (int, optional): Index of the subsection to get. Defaults to 0.
        strip (bool, optional): True to strip leading and trailing whitespace
            from the result, False otherwise.

    Returns:
        str
    """
    try:
        sect = section[ind]
    except:
        return ""
    else:
        return sect.strip() if strip else sect
