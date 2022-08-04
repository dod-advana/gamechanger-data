import re
import typing as t
from collections import defaultdict

from gamechangerml.src.featurization.ref_utils import make_dict

ref_regex = make_dict()


def look_for_general(
    m_str: str,
    ref_dict: defaultdict,
    base_num: t.Pattern[str],
    full_num: t.Pattern[str],
    doc_type: str,
) -> defaultdict:
    """
    Reference Extraction by Regular Expression: For general use

    Args:
        m_str: text string to search
        ref_dict: dictionary of references to be updated
        base_num: regex for the numerical part of reference
        full_num: regex for the full reference
        doc_type: prefix for number when saving reference for uniformity

    Returns:
        updated ref_dict with the references found and their counts
    """
    # Example for dodm
    # base_num = re.compile(r"(([A-Z]+-)?[0-9]{4}\.\s*[0-9]{1,3}\s*(-[A-Z]+)?([E])?)",re.IGNORECASE) # Example: 5025.01 or 5025.01

    # Example DODM
    # dodm_full_num = re.compile(r"(((dod manual)|(dodm))\s*[0-9]{4}\.\s*[0-9]{1,3}(\s*,*\s*Volume\s*[0-9]+)?)",re.IGNORECASE) #Example: dod directive 5025.01, Volume 1 or  case insensitive

    directive = full_num.findall(m_str)

    if directive is not None:
        for match in directive:
            num_match = base_num.search(match[0])
            if not num_match:
                continue
            ref = (str(doc_type) + " " + str(num_match[0])).strip()
            ref_dict[ref] += 1
    return ref_dict


def collect_ref_list(text: str) -> defaultdict:
    """
    Collection of all reference function calls

    Args:
        text: the text to be searched for references as a string

    Returns:
        ref_dict with all references and their counts
    """
    ref_dict = defaultdict(int)
    text = text.replace("\n", "")
    # allows regex to interpret the unicode as a -
    text = text.replace("\u2013", "-")
    text = re.sub(r"[()]", " ", text)

    for key, value in ref_regex.items():
        base = value[0]
        full = value[1]
        ref_dict = look_for_general(text, ref_dict, base, full, key)
    return ref_dict


def add_ref_list(doc_dict):
    iss_ref = collect_ref_list(doc_dict["text"])
    doc_dict["ref_list"] = list(iss_ref)
    return doc_dict
