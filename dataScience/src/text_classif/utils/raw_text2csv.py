# The MIT License (MIT)
# Subject to the terms and conditions contained in LICENSE
import datetime
import fnmatch
import logging
import json
import os
import re

import numpy as np
import pandas as pd
from tqdm import tqdm
import dataScience.src.utilities.spacy_model as spacy_m
import dataScience.src.text_classif.utils.classifier_utils as cu


logger = logging.getLogger(__name__)
here = os.path.dirname(os.path.realpath(__file__))


def new_df():
    return pd.DataFrame(columns=["src", "label", "sentence"])


def make_sentences(text, src_, nlp):
    sents = [cu.scrubber(s.text) for s in nlp(text).sents]
    df = new_df()
    for sent in sents:
        df = df.append({"src": src_, "label": 0, "sentence": sent},
                       ignore_index=True)
    return df


def raw2df(src_path, glob, nlp, out_df):
    for raw_text, fname in cu.gen_gc_docs(src_path, glob, key="raw_text"):
        sent_df = make_sentences(raw_text, fname, nlp)
        out_df = out_df.append(sent_df, ignore_index=True)
        logger.info("{:>25s} : {:>3,d}".format(fname, len(sent_df)))
    return out_df


def main(src_path, glob, output_csv):
    logger.info("loading spaCy")
    nlp = spacy_m.get_lg_vectors()
    nlp.add_pipe(nlp.create_pipe('sentencizer'))
    output_df = new_df()
    out_df = raw2df(src_path, glob, nlp, output_df)
    out_df.to_csv(output_csv, header=False, index=False)


if __name__ == "__main__":
    from argparse import ArgumentParser

    log_fmt = (
            "[%(asctime)s %(levelname)-8s], [%(filename)s:%(lineno)s - "
            + "%(funcName)s()], %(message)s"
    )
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    parser = ArgumentParser(prog="python raw_text2csv.py",
                            description="csv of each sentence in a json doc")
    parser.add_argument(
        "-i",
        "--input-path",
        dest="input_path",
        type=str,
        help="corpus path"
    )
    parser.add_argument(
        "-o",
        "--output-csv",
        dest="output_csv",
        type=str,
        help="output .csv path, name"
    )
    parser.add_argument(
        "-g",
        "--glob",
        dest="glob",
        help="file pattern to match"
    )
    args = parser.parse_args()

    main(args.input_path, args.glob, args.output_csv)
