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


def squash_whitespace_to_spaces(_s: str) -> str:
    """Squashes all consecutive whitespace characters into a single space character"""
    return re.sub(pattern=r"\s+", repl=r' ', string=_s)


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


DEFAULT_TRANSFORMER_PIPELINE = [
    translate_to_ascii_string,
    translate_double_quotes_to_single_quotes,
    translate_bad_characters_to_underscores,
    squash_underscores,
    squash_whitespace_to_spaces,
    squash_non_word_characters,
    drop_underscores_around_words,
]


def transform_string(
    input_string: str,
    ordered_string_transformers: Iterable[
        Callable[[str], str]
    ],
) -> str:
    """Translates arbitrary utf-8 name into one that conforms to a specific set of chars
    :param input_string: string that's meant to be processed through the pipeline
    :param ordered_string_transformers: iterable of transformers that serve as pipeline for processing input string

    :returns: transformed string
    """

    processed_string = str_chain_apply(
        input_str=input_string, ordered_transformers=ordered_string_transformers
    )

    return processed_string


def normalize_string(input_string: str) -> str:
    """Apply default transformations to normalize the string"""
    return transform_string(input_string=input_string, ordered_string_transformers=DEFAULT_TRANSFORMER_PIPELINE)