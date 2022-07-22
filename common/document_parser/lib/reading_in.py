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
import chardet

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
    Reading Plain text file. Attempts to guess the correct encoding, else falls back to latin1.

    Args:
        fname: name of text file

    Returns:
        text string from file
    """
    with open(fname, 'r', encoding='utf-8-sig', errors='ignore') as f_in:
        text_bytes = f_in.read().encode()
    encoding = chardet.detect(text_bytes)['encoding'] or 'latin1'
    return text_bytes.decode(encoding)
