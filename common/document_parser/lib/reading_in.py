# auxillary to read in arbitrary file types

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


def read_doc_dict(fname: Path) -> defaultdict:
    """
    Reading in Json format for extraction

    Args:
        fname: name of json file

    Returns:
        dictionary of json contents
    """
    with open(fname) as f_in:
        doc_dict = json.load(f_in)

    return doc_dict


def read_plain_text(fname: Path) -> str:
    """
    Reading Plain text file

    Args:
        fname: name of text file

    Returns:
        text string from file
    """
    with open(fname) as f_in:
        text = f_in.read()

    return text
