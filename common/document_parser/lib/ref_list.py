import re
from collections import defaultdict
from typing import Pattern, List
import typing as t

from common.document_parser.ref_utils import make_dict, preprocess_text


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
            values = [x for x in match if x != ""]
            if len(values) != 1:
                print(
                    f"ERR: Patterns in `ref_regex` should only have exactly 1 "
                    f"non-empty capture group each. Check the pattern for {doc_type}"
                )
                print("text was:", text)
                print("match was:", match)
                continue
            match = values[0]
        elif match == "":
            continue

        if doc_type == "Title":
            try:
                num = int(match.strip())
            except:
                continue
            else:
                if num > 53 or num == 0:
                    continue
        elif doc_type == "CFR Title":
            try:
                num = int(match.strip())
            except:
                continue
            else:
                if num > 50 or num == 0:
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
    text = preprocess_text(text)

    for ref_type, pattern in ref_regex.items():
        ref_dict = look_for_general(text, ref_dict, pattern, ref_type)

    return ref_dict


def add_ref_list(doc_dict):
    iss_ref = collect_ref_list(doc_dict["text"])
    doc_dict["ref_list"] = list(iss_ref)
    return doc_dict
