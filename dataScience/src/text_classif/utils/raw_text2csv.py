"""
usage: python raw_text2csv.py [-h] [-i INPUT_PATH] [-o OUTPUT_CSV] [-g GLOB]

csv of each sentence in the text

optional arguments:
  -h, --help            show this help message and exit
  -i INPUT_PATH, --input-path INPUT_PATH
                        corpus path
  -o OUTPUT_CSV, --output-csv OUTPUT_CSV
                        output path for .csv files
  -g GLOB, --glob GLOB  file pattern to match

"""
# The MIT License (MIT)
# Subject to the terms and conditions contained in LICENSE
import logging
import os

import pandas as pd

import dataScience.src.text_classif.utils.classifier_utils as cu
import dataScience.src.utilities.spacy_model as spacy_m

logger = logging.getLogger(__name__)
here = os.path.dirname(os.path.realpath(__file__))


def new_df():
    return pd.DataFrame(columns=["src", "label", "sentence"])


def make_sentences(text, src, nlp):
    sents = [cu.scrubber(s.text) for s in nlp(text).sents]
    df = new_df()
    for sent in sents:
        df = df.append(
            {"src": src, "label": 0, "sentence": sent}, ignore_index=True
        )
    return df


def raw2df(src_path, glob, key="raw_text"):
    for raw_text, fname in cu.gen_gc_docs(src_path, glob, key=key):
        sent_df = cu.make_sentences(raw_text, fname)
        logger.info("{:>25s} : {:>5,d}".format(fname, len(sent_df)))
        yield sent_df, fname


def main(src_path, glob, output_path):
    """
    See the docstring for an explanation of the arguments.

    For the target document(s), sentences are extracted from the `raw_text`
    and passed through spaCy's `sentencizer`. Each sentence is a dictionary
    of the document's source name, `src`, `sentence`, and `label`. Each
    `label` is `0`.

    The resulting list of dictionaries is written to a `.csv` file, one file
    per document. The `.csv` file name consists of the original filename with
    `_sentences` appended. For example, `DoDM_1145.02.sentences.csv`.

    Returns:
        None
    """
    # TODO   spaCy will fail when the text is very large. Iterate through
    # TODO   the raw_text of each paragraph as a remedy. Use
    logger.info("loading spaCy")
    nlp = spacy_m.get_lg_vectors()
    nlp.add_pipe(nlp.create_pipe("sentencizer"))

    fname = None
    output_df = new_df()
    try:
        for sent_df, fname in raw2df(src_path, glob):
            output_df = output_df.append(sent_df, ignore_index=True)
            base, ext = os.path.splitext(os.path.basename(fname))
            output_csv = base.replace(" ", "_") + "_sentences" + ".csv"
            output_csv = os.path.join(output_path, output_csv)
            output_df.to_csv(output_csv, header=True, index=False)
            output_df = new_df()
    except (FileNotFoundError, IOError) as e:
        logger.exception("offending file : {}".format(fname))
        raise e


if __name__ == "__main__":
    from argparse import ArgumentParser

    log_fmt = (
        "[%(asctime)s %(levelname)-8s], [%(filename)s:%(lineno)s - "
        + "%(funcName)s()], %(message)s"
    )
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    parser = ArgumentParser(
        prog="python raw_text2csv.py",
        description="csv of each sentence in the text",
    )
    parser.add_argument(
        "-i", "--input-path", dest="input_path", type=str, help="corpus path"
    )
    parser.add_argument(
        "-o",
        "--output-csv",
        dest="output_csv",
        type=str,
        default=None,
        help="output path for .csv files",
    )
    parser.add_argument(
        "-g", "--glob", dest="glob", help="file pattern to match"
    )
    args = parser.parse_args()

    main(args.input_path, args.glob, args.output_csv)
