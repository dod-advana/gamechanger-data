"""
This module contains functions to extract references inside of documents using regular expressions
"""

import re
import json
import argparse
from pathlib import Path
from common.document_parser.ref_utils import make_dict
from collections import defaultdict
from typing import Pattern, List
import typing as t

ref_regex = make_dict()


def look_for_general(m_str:str, ref_dict:defaultdict, base_num: t.Pattern[str], full_num: t.Pattern[str], doc_type:str)->defaultdict:
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


def collect_ref_list(text:str)->defaultdict:
    """
    Collection of all reference function calls

    Args:
        text: the text to be searched for references as a string

    Returns:
        ref_dict with all references and their counts
    """
    ref_dict = defaultdict(int)
    text = text.replace("\n", "")
    text = text.replace("\u2013","-") #allows regex to interpret the unicode as a - 
    text = re.sub(r"[()]", " ", text)

    for key, value in ref_regex.items():
        base = value[0]
        full = value[1]
        ref_dict = look_for_general(text, ref_dict, base, full, key)
    return ref_dict


def read_doc_dict(fname:Path)->defaultdict:
    """
    Reading in Json format for extraction

    Args:
        fname: name of json file

    Returns:
        dictionary of json contents
    """
    with open(fname) as f_in:
        doc_dict=json.load(f_in)

    return doc_dict


def read_plain_text(fname:Path)->str:
    """
    Reading Plain text file

    Args:
        fname: name of text file

    Returns:
        text string from file
    """
    with open(fname) as f_in:
        text=f_in.read()

    return text
