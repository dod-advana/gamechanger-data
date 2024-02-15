import logging
import re
import numpy as np
from itertools import groupby
from string import punctuation
from typing import Union, List, Dict, Tuple

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


def simple_clean(text: str) -> str:
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
                # paragraph = filter_sentences(paragraph)
                good_pars.append(paragraph)

        final_text = "\n".join(good_pars)
        return final_text
    except UnicodeDecodeError:
        raise


def utf8_pass(text: str) -> str:
    return text.encode("utf-8", "ignore").decode("utf-8")


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


# Source: https://rajpurkar.github.io/SQuAD-explorer/
def normalize_answer(s: str) -> str:
    """
    Normalize answers for QA evaluation.
    Lower text and remove punctuation, articles and extra whitespace.
    """

    def remove_articles(text):
        regex = re.compile(r"\b(a|an|the)\b", re.UNICODE)
        return re.sub(regex, " ", text)

    def white_space_fix(text):
        return " ".join(text.split())

    def remove_punc(text):
        exclude = set(punctuation)
        return "".join(ch for ch in text if ch not in exclude)

    def lower(text):
        return text.lower()

    return white_space_fix(remove_articles(remove_punc(lower(s))))


def normalize_query(s: str) -> str:
    """
    Normalize queries.
    Lower text and remove extra whitespace.
    """

    def white_space_fix(text):
        return " ".join(text.strip().lstrip().split())

    def lower(text):
        return text.lower()

    def remove_quotes(text):
        exclude = ["'", '"']
        return "".join(ch for ch in text if ch not in exclude)

    return white_space_fix(remove_quotes(lower(s)))


def get_tokens(s: str) -> List[str]:
    """Get tokens from normalized answer."""
    if not s:
        return []
    return s.split()


def has_many_short_tokens(processed_tokens, threshold):
    """Checks if the median length of tokens is less than the expected threshold"""
    median_len = np.median([len(i) for i in processed_tokens])
    if median_len <= threshold:
        return True
    else:
        return False


def has_many_repeating(text, tokens, threshold):
    """Checks if the ratio of unique tokens is less than an expected threshold"""
    ratio_unique = len(set(tokens)) / len(text.split(" "))
    if ratio_unique < threshold:
        return True
    else:
        return False


def has_extralong_tokens(text, threshold):
    """Checks if the paragraph has a high percentage of (nonwebsite) tokens exceeding threshold for normal token length"""
    websites = ["http", "www."]
    tokens = [i for i in text.split(" ") if i[:4] not in websites]
    long_tokens = [i for i in tokens if len(i) > threshold]
    if len(long_tokens) / len(tokens) > 0.05:
        return True
    else:
        return False


def is_a_toc(text):
    """Checks if a paragraph appears to be a table of contents"""
    toc_separation = re.findall(r"(\.{6,})", text)
    if len(toc_separation) > 0:
        return True
    else:
        return False


def majority_tokens_filtered(tokens, text):
    """Checks if most of the tokens were filtered out after processing"""
    if (len(tokens) / len(text.split(" "))) <= 0.5:
        return True
    else:
        return False


def check_quality_paragraph(tokens, text):
    """Runs filter functions to check that a paragraph isn't a junk paragraph"""

    if majority_tokens_filtered(tokens, text):
        return False
    if has_many_short_tokens(tokens, threshold=2.5):
        return False
    elif has_many_repeating(text, tokens, threshold=0.2):
        return False
    elif has_extralong_tokens(text, threshold=25):
        return False
    elif is_a_toc(text):
        return False
    else:
        return True


# Adapted from https://www.datacamp.com/community/tutorials/fuzzy-string-python
def levenshtein_ratio_and_distance(
    s: str, t: str, ratio_calc: bool = False
) -> Tuple[int, float]:
    """levenshtein_ratio_and_distance:
    Calculates levenshtein distance between two strings.
    If ratio_calc = True, the function computes the
    levenshtein distance ratio of similarity between two strings
    For all i and j, distance[i,j] will contain the Levenshtein
    distance between the first i characters of s and the
    first j characters of t
    """
    # Initialize matrix of zeros
    rows = len(s) + 1
    cols = len(t) + 1
    distance = np.zeros((rows, cols), dtype=int)

    # Populate matrix of zeros with the indeces of each character of both strings
    for i in range(1, rows):
        for k in range(1, cols):
            distance[i][0] = i
            distance[0][k] = k

    # Iterate over the matrix to compute the cost of deletions,insertions and/or substitutions
    for col in range(1, cols):
        for row in range(1, rows):
            if s[row - 1] == t[col - 1]:
                cost = 0  # If the characters are the same in the two strings in a given position [i,j] then the cost is 0
            else:
                # In order to align the results with those of the Python Levenshtein package, if we choose to calculate the ratio
                # the cost of a substitution is 2. If we calculate just distance, then the cost of a substitution is 1.
                if ratio_calc == True:
                    cost = 2
                else:
                    cost = 1
            distance[row][col] = min(
                distance[row - 1][col] + 1,  # Cost of deletions
                distance[row][col - 1] + 1,  # Cost of insertions
                distance[row - 1][col - 1] + cost,
            )  # Cost of substitutions
    Ratio = ((len(s) + len(t)) - distance[row][col]) / (len(s) + len(t))

    return distance[row][col], Ratio


def string_contains(str1: str, str2: str) -> bool:
    """Checks if a str2 contains str1"""
    set1 = str1.lower().split()
    set2 = str2.lower().split()
    if len(set(set1).intersection(set2)) == len(set1):
        return True
    else:
        return False


def check_majority_numbers(query: str, ratio: float = 0.6) -> bool:
    """Checks ratio of numerical characters in a string, True if ratio is less than ratio threshold"""

    if len(re.sub(r"[0-9]", "", query)) / len(query) <= ratio:
        return True
    else:
        return False


def sort_first(samples: List[str]) -> Dict[str, List[str]]:
    """Makes a dictionary of first letter: string for faster lookup of strings"""

    doc_dict = {}
    docs = []
    first_letters = []
    for i in list(set(samples)):
        if type(i) == str:
            first_letters.append(str(i)[0].lower())
            docs.append(i)
    zipped = dict(zip(docs, first_letters))
    for i, v in zipped.items():
        doc_dict[v] = [i] if v not in doc_dict.keys() else doc_dict[v] + [i]

    return doc_dict


def filter_title_queries(queries: List[str], doc_ids: List[str]) -> List[str]:
    """Collects list of queries that appear in a list of doc_ids/appear to look like doc_ids"""

    remove = []
    logger.info("Making dictionary for doc titles")
    doc_dict = sort_first(doc_ids)
    logger.info("*** Comparing queries to doc titles\n")
    for i in queries:
        if not re.search("[a-zA-Z]", i):  ## if the query has no letters, remove
            logger.info(f"*** Removing query: {i} // (contains no characters)")
            remove.append(i)
        elif re.search(
            "[0-9]", i
        ):  ## if there are numbers in the query, compare to titles
            if i.lower() in list(set([q.lower() for q in doc_ids])):
                logger.info(f"*** Removing query: {i} // (in doc ids)")
                remove.append(i)
            elif check_majority_numbers(i):
                logger.info(f"*** Removing query: {i} // (majority numbers)")
                remove.append(i)
            else:
                try:
                    cleaned = i.upper().replace("'", "")
                    start = cleaned[0].lower()  # starting letter
                    sub = doc_dict[start]
                    for x in sub:
                        if string_contains(cleaned, x):
                            logger.info(
                                f"*** Removing query: {i} // (string inside string)"
                            )
                            remove.append(i)
                            break
                        else:
                            dist, ratio = levenshtein_ratio_and_distance(
                                cleaned.lower(), x.lower()
                            )
                            if len(i) > 12 and ratio >= 0.75:
                                logger.info(
                                    f"*** Removing query: {i} // ({dist} char, {ratio} ratio diff from doc title)"
                                )
                                remove.append(i)
                                break
                            elif len(i) < 12 and dist <= 2:
                                logger.info(
                                    f"*** Removing query: {i} // ({dist} char, {ratio} ratio diff from doc title)"
                                )
                                remove.append(i)
                                break
                except Exception as e:
                    logger.info(f"Skipping {i}")

    logger.info(f"*** Collected {str(len(remove))} queries to remove")
    return remove
