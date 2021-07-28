import logging
import re
from itertools import groupby
from string import punctuation
from typing import Union, List

from spacy.lang.en import English

logger = logging.getLogger(__name__)

punct = set(punctuation)


def translate_to_ascii_string(_s: Union[str, bytes]) -> str:
    """
    Translates utf-8 byte sequence to ASCII string
    The point is to approximately translate foreign characters rather than
    deleting them
    Args:
        _s (str|bytes: string to translate

    Returns:
        str

    Raises:
        UnicodeDecodeError if decoding fails

    """
    _str_bytes = _s if isinstance(_s, bytes) else _s.encode("utf-8", "ignore")
    return _str_bytes.decode("ascii", errors="ignore")


def simple_clean(text):
    """
    Performs a simple text cleaning: removes newline characters, square and
    curly braces, insures `utf-8` encoding, and reduces inter-word spacing to
    a single space.

    Args:
        text (str): text to be cleaned

    Returns:
        str

    Raises:
        UnicodeDecodeError if an illegal Unicode code-point is encountered

    """
    try:
        text = re.sub("[\\n\\t\\r]+", " ", text)
        text = re.sub("[" + re.escape("][}{)\\/") + "]+", " ", text)
        text = re.sub("\\s{2,}", " ", text)
        text = translate_to_ascii_string(text)
        return text.strip()
    except UnicodeDecodeError as e:
        logger.exception("{}: {}".format(type(e), str(e)), exc_info=True)
        raise


def split_sentences(text: str) -> List[str]:
    """
    Splitting sentences with spacy.
    """

    nlp = English()
    nlp.add_pipe(nlp.create_pipe("sentencizer"))  # updated
    doc = nlp(text)

    return [sent.string.strip() for sent in doc.sents]


def ratio_caps(text: str, ratio: float) -> bool:
    """
    Checks the ratio of capital letters to words in a sentence
    ##TO DO: better way to clean. placeholder for removing DISTRIBUTION
    STATEMENTS/jargon fragments
    """
    if len(re.findall(r"[A-Z]", text)) / len(text.split()) < ratio:
        return True
    else:
        return False


def filter_sentences(text: str, token_len: int = 5, ratio: float = 1.5) -> str:
    """
    Filters out sentences shorter than 6 words long with high caps-to-words i
    ratio (if greater than 1.5)
    """
    sentences = split_sentences(text)
    filter_short = [i for i in sentences if len(i.split()) > token_len]
    filter_caps = [i for i in filter_short if ratio_caps(i, ratio)]

    return " ".join(filter_caps)


def summary_clean(text: str, min_par_len=15) -> str:
    """
    Based on original function in summary.py for cleaning paragraphs before
    creating the summary.

    Args:
        min_par_len:
        text (str): text to be cleaned.

    Returns:
        str

    """
    try:
        text = translate_to_ascii_string(text)
        # remove parenthesis and things contained in them
        text = re.sub(r"\(.*?\)", "", text)
        # remove list indicators i.e. 1. a. etc.
        text = re.sub(r"\b\w\.", "", text)
        # remove bullet points
        text = re.sub("\u2022", "", text)
        text = re.sub(r"^https?:\/\/.*[\r\n]*", "", text, flags=re.MULTILINE)

        newtext = []
        for k, g in groupby(text):
            if k in punct:
                newtext.append(k)
            else:
                newtext.extend(g)
        text = "".join(newtext)  # remove excess punctuation
        pars = re.split("\r?\n(?:\\s*\r?\n)+", text)
        good_pars = []
        # get only paragraphs of significant length
        for paragraph in pars:
            if len(paragraph.split()) > min_par_len:
                #paragraph = filter_sentences(paragraph)
                good_pars.append(paragraph)

        final_text = "\n".join(good_pars)
        return final_text
    except UnicodeDecodeError:
        raise


def utf8_pass(text):
    return text.encode('utf-8', 'ignore').decode('utf-8')


def clean_text(doc_text: str) -> str:
    """
    The text is cleaned from special characters and extra spaces
    Args:
        doc_text: input text to be cleaned

    Returns:

    """

    text = doc_text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    remove = punctuation + "”“"
    remove = remove.replace(".", "")

    text = text.translate({ord(i): None for i in remove})

    return text
