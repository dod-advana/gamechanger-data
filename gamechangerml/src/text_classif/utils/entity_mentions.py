"""
usage: python entity_mentions.py [-h] -i INPUT_PATH -e ENTITY_FILE -o
                                 OUTPUT_JSON -g GLOB

outputs counts of entity mentions in each document; brute force is used

optional arguments:
  -h, --help            show this help message and exit
  -i INPUT_PATH, --input-path INPUT_PATH
                        corpus path
  -e ENTITY_FILE, --entity-file ENTITY_FILE
                        list of entities with their abbreviations
  -o OUTPUT_JSON, --output-json OUTPUT_JSON
                        output path for .csv files
  -g GLOB, --glob GLOB  file pattern to match
"""
import json
import logging
import os
import re
import time
from collections import defaultdict

import numpy as np
import pandas as pd
from tqdm import tqdm

import gamechangerml.src.text_classif.utils.classifier_utils as cu

logger = logging.getLogger(__name__)


def make_entity_re(entity_csv):
    """
    Creates regular expressions for long form entities and their abbreviations,
    if they exist. These are large alternations. No magic.

    Args:
        entity_csv (str): csv with entries consiting of
            *entity name*, *entity abbreviation*, *entity type*

    Returns:
        SRE_Pattern, SRE_Pattern
    """
    if not os.path.isfile(entity_csv):
        raise FileNotFoundError("can't find {}".format(entity_csv))
    df = pd.read_csv(entity_csv, names=["long_form", "short_form", "etype"])
    df = df.replace(np.nan, "")

    entities = list(set(df["long_form"]))
    abbrvs = list(set(df["short_form"]))

    logger.info("num entities : {}".format(len(entities)))
    logger.info(" num abbrevs : {}".format(len(abbrvs)))

    entities.sort(key=lambda s: len(s), reverse=True)
    abbrvs.sort(key=lambda s: len(s), reverse=True)

    entity_re = "|".join([re.escape(e.strip()) for e in entities])
    entity_re = re.compile("(\\b" + entity_re + "\\b)", re.I)

    abbrv_re = "|".join(([re.escape(a.strip()) for a in abbrvs if a.strip()]))
    abbrv_re = re.compile("(\\b" + abbrv_re + "\\b)")
    return abbrv_re, entity_re


def contains_entity(text, entity_re, abbrv_re):
    """
    Finds all the entities in the text, returning a list with every
    instance of the entity. If no entities are found, an empty list is
    returned.

    Args:
        text (str): text to search
        entity_re (SRE_Pattern): compiled regular expression
        abbrv_re (SRE_Pattern): compiled regular expression

    Returns:
        List[str]
    """
    entity_list = list()

    entities = entity_re.findall(text)
    if entities:
        entity_list.extend(entities)

    abbrvs = abbrv_re.findall(text)
    if abbrvs:
        for a in abbrvs:
            entity_list.append(a)
    return entity_list


def entities_spans(text, entity_re, abbrv_re):
    """
    Finds all the entities in the text, returning a list with every
    instance of the entity. If no entities are found, an empty list is
    returned.

    Args:
        text (str): text to search
        entity_re (SRE_Pattern): compiled regular expression
        abbrv_re (SRE_Pattern): compiled regular expression

    Returns:
        List[tuple]
    """
    ent_list = list()
    for mobj in entity_re.finditer(text):
        entity_span = (mobj.group(), (mobj.start(), mobj.end()))
        ent_list.append(entity_span)

    for mobj in abbrv_re.finditer(text):
        entity_span = (mobj.group(), (mobj.start(), mobj.end()))
        ent_list.append(entity_span)
    return ent_list


def count_glob(corpus_dir, glob, entity_re, abbrv_re):
    """
    For each matching document, list each entity and its frequency of
    occurrence.

    Args:
        corpus_dir (str): directory containing the corpus
        glob (str): file matching glob
        entity_re (SRE_Pattern): compiled regular expression for long forms
        abbrv_re (SRE_Pattern): compiled regular expression for short forms

    Returns:
        Dict[List[tuple]] : key is the document name, each tuple is
            (entity, frequency)
    """
    SENT = "sentence"
    nfiles = cu.nfiles_in_glob(corpus_dir, glob)
    entity_count = defaultdict(int)
    doc_entity = dict()

    r2d = cu.raw2dict(corpus_dir, glob)
    for sent_dict, fname in tqdm(r2d, total=nfiles, desc="docs"):
        for sd in sent_dict:
            sent = sd[SENT]
            ent_list = contains_entity(sent, entity_re, abbrv_re)
            for ent in ent_list:
                entity_count[ent.strip()] += 1
        doc_entity[fname] = sorted(
            entity_count.items(), key=lambda x: x[1], reverse=True
        )
        entity_count = defaultdict(int)
    return doc_entity


def entity_mentions_glob(entity_file, corpus_dir, glob):
    """
    Wrapper for `count_glob()`.

    Args:
        entity_file (str): entity / abbreviation files
        corpus_dir (str): corpus directory
        glob (str): file matching expression

    Returns:
        Dict[List[tuple]] : key is the document name, each tuple is
            (entity, frequency)
    """
    abbvs, ents = make_entity_re(entity_file)
    return count_glob(corpus_dir, glob, ents, abbvs)


def entities_from_raw(entity_file, corpus_dir, glob):
    """
    Finds each occurrence of an entity with its span.

    Args:
        entity_file (str): entity / abbreviation files
        corpus_dir (str): corpus directory
        glob (str): file matching

    Returns:
       str, List[tuple, tuple]
    """
    abbrv_re, entity_re = make_entity_re(entity_file)
    for fname, json_doc in cu.gen_gc_docs(corpus_dir, glob):
        text = json_doc["raw_text"]
        entity_spans = entities_spans(text, entity_re, abbrv_re)
        yield fname, entity_spans


def entities_and_spans(entity_file, corpus_dir, glob):
    """
    Wrapper for `entities_from_raw()`
    Args:
        entity_file (str): entity / abbreviation files
        corpus_dir (str): corpus directory
        glob (str): file matching

    Returns:
        Dict[List, tuple(tuple)]
    """
    nfiles = cu.nfiles_in_glob(corpus_dir, glob)
    entity_span_d = dict()
    efr = entities_from_raw(entity_file, corpus_dir, glob)
    for fname, entity_spans in tqdm(efr, total=nfiles):
        entity_span_d[fname] = entity_spans
    return entity_span_d


if __name__ == "__main__":
    from argparse import ArgumentParser
    import gamechangerml.src.text_classif.utils.log_init as li

    li.initialize_logger(to_file=False, log_name="none")

    fp = os.path.split(__file__)
    fp = "python " + fp[-1]
    parser = ArgumentParser(
        prog=fp,
        description="brute force counting of entity mentions in each document",
    )
    parser.add_argument(
        "-i",
        "--input-path",
        dest="input_path",
        type=str,
        help="corpus path",
        required=True,
    )
    parser.add_argument(
        "-e",
        "--entity-file",
        dest="entity_file",
        type=str,
        help="list of entities with their abbreviations",
        required=True,
    )
    parser.add_argument(
        "-o",
        "--output-json",
        dest="output_json",
        type=str,
        required=True,
        help="output path for .csv files",
    )
    parser.add_argument(
        "-g",
        "--glob",
        dest="glob",
        type=str,
        required=True,
        help="file pattern to match",
    )
    parser.add_argument(
        "-s",
        "--spans",
        dest="spans",
        action="store_true",
        help="find spans for each entity occurrence",
    )
    args = parser.parse_args()

    start = time.time()
    if args.spans:
        output = entities_and_spans(
            args.entity_file, args.input_path, args.glob
        )
    else:
        output = entity_mentions_glob(
            args.entity_file, args.input_path, args.glob
        )
    if output:
        output = json.dumps(output)
        with open(args.output_json, "w") as f:
            f.write(output)
        logger.info("output written to : {}".format(args.output_json))
    else:
        logger.warning("no output produced")

    logger.info("time : {:}".format(cu.format_time(time.time() - start)))
