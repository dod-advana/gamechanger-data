from calendar import month_name

MONTH_LIST = [m for m in month_name[1:]]

# UPPERCASE or TitleCase "enclosure" used in regex patterns.
CAPITAL_ENCLOSURE = r"E(?:nclosure|NCLOSURE)"


DD_MONTHNAME_YYYY = rf"""
        (?:[0-2]?[0-9]|3[01])                       # 1-2 digit day
        [ ]                                         # Single space
        (?:{'|'.join(MONTH_LIST)})                  # Full month name
        [ ]                                         # Single space
        [0-9]{{4}}                                  # 4 digits (year)
"""


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
