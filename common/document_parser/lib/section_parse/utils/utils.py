from re import match, IGNORECASE
from typing import Union


def is_alpha_list_item(text: str) -> bool:
    """Check if `text` is an item of an alphabetical list."""
    # Ex: "a. ", "b) ", "(c) "
    return (
        match(r"[a-z]{1,2}\.\s|\(?[a-z]{1,2}\)\s", text, flags=IGNORECASE)
        is not None
    )


def match_num_list_item(text: str) -> Union[str, None]:
    """If the text starts with number list formatting, returns the number as a
    string. Otherwise, returns None. Supports up to 2 digits.
    """
    # Ex: "1.", "2)"
    num = match(r"\(?([0-9]{1,2})[\.\)]", text)

    return num.groups()[0] if num else None
