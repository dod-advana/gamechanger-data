import re
from typing import Union, Callable, Iterable


def str_chain_apply(
    input_str: str, ordered_transformers: Iterable[Callable[[str], str]]
) -> str:
    """Apply set of functions in order - pipeline-like"""
    result = input_str
    for t in ordered_transformers:
        result = t(result)
    return result


def translate_to_ascii_string(_s: Union[str, bytes]) -> str:
    """Translates utf-8 byte sequence to ASCII string
    The point is to approximately translate foreign characters rather than deleting them
    """
    _str_bytes = _s if isinstance(_s, bytes) else _s.encode("utf-8")
    return _str_bytes.decode("ascii", errors="ignore")


def fix_utf8_string(_s: Union[str, bytes]) -> str:
    """Translates utf-8 byte sequence to one without invalid utf-8 characters"""
    _str_bytes = _s if isinstance(_s, bytes) else _s.encode("utf-8")
    return _str_bytes.decode('utf-8', errors='ignore')


def squash_whitespace_to_spaces(_s: str) -> str:
    """Squashes all consecutive whitespace characters into a single space character"""
    return re.sub(pattern=r"\s+", repl=r' ', string=_s)


def remove_plus_signs(_s: str) -> str:
    """Removes plus signs from string"""
    return re.sub(pattern=r'\+', repl=r'', string=_s)


def translate_double_quotes_to_single_quotes(_s: str) -> str:
    """Translate double quotes to single quotes"""
    return re.sub(pattern=r'"', repl=r"'", string=_s)


def translate_bad_characters_to_underscores(_s: str) -> str:
    """Translates bad characters to underscores...
    ...in order to preserve separation qualities of bad characters.
    For example: 'Thisµthat' becomes 'This_that'"""
    return re.sub(pattern=r"""[^0-9a-zA-Z_ ',&.-]""", repl="_", string=_s)


def squash_underscores(_s: str) -> str:
    """squash consecutive underscores into singular ones"""
    return re.sub(pattern=r"(_)+", repl=r"\1", string=_s)


def squash_non_word_characters(_s: str) -> str:
    """Squashes certain consecutive characters into singular characters"""
    return re.sub(pattern=r"""(\W)+""", repl=r"\1", string=_s)


def drop_underscores_around_words(_s: str) -> str:
    """Trims underscores surrounding words"""
    return re.sub(pattern=r"(\b_\B|\B_\b)", repl="", string=_s)


def trim_string(_s: str, length: int) -> str:
    """Shortens string to 100 characters or less"""
    if len(_s) <= length:
        return _s
    else:
        return " ".join(_s[:length + 1].split(" ")[:-1])


def size_fmt(num: float, suffix='B') -> str:
    """Returns readable str form of given size number (e.g. bytes) in more readable higher form, e.g. 1_000_000 -> 976.6KiB"""
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)