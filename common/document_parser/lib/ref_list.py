import re
from collections import defaultdict

from common.document_parser.ref_utils import make_dict


ref_regex = make_dict()


def look_for_general(text, ref_dict, pattern, doc_type):
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
    matches = pattern.findall(text)

    for match in matches:
        if type(match) == tuple:
            print(
                f"ERR: Patterns in `ref_regex` should only have 1 capture "
                f"group each. Check the pattern for {doc_type}"
            )
            continue
        elif match == "":
            continue
        ref = (doc_type + " " + match).strip()
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
    # Interpret the unicode as a -
    text = text.replace("\u2013", "-")
    text = re.sub(r"[()]", " ", text)
    # Normalize whitespace here so regex search is simpler
    text = " ".join(text.split())

    for ref_type, pattern in ref_regex.items():
        ref_dict = look_for_general(text, ref_dict, pattern, ref_type)

    return ref_dict


def add_ref_list(doc_dict):
    iss_ref = collect_ref_list(doc_dict["text"])
    doc_dict["ref_list"] = list(iss_ref)
    return doc_dict
