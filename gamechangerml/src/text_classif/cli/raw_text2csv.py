"""
usage: python raw_text2csv.py [-h] -i INPUT_PATH -o OUTPUT_CSV -g GLOB

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

import gamechangerml.src.text_classif.utils.classifier_utils as cu

logger = logging.getLogger(__name__)


def new_df():
    return pd.DataFrame(columns=["src", "label", "sentence"])


def raw2df(src_path, glob, key="raw_text"):
    """
    Reads a .json corpus document, extracts the `key`, and generates a list
    of dictionaries. Each dictionary contains one sentence, as follows:

        {'src': "file.csv", 'sentence': "some passage", "label": 0}

    Args:
        src_path (str): directory containing the corpus `.json` documents
        glob (str): file glob, e.g., DoDI*.json
        key (str): defaults to "raw_text". This should not be changed.

    Yields:
        List[Dict]

    """
    for fname, doc in cu.gen_gc_docs(src_path, glob, key=key):
        if key in doc:
            raw_text = doc[key]
            sent_df = cu.make_sentences(raw_text, fname)
            logger.info("{:>35s} : {:>5,d}".format(fname, len(sent_df)))
            yield sent_df, fname
        else:
            logger.warning("no key '{}' in {}".format(key, fname))


def raw_text2csv(src_path, glob, output_path):
    """
    See the docstring for an explanation of the arguments.

    For the target document(s), sentences are extracted from the `raw_text`
    and passed through a sentence tokenizer. Each sentence is a dictionary
    of the document's source name, `src`, `sentence`, and `label`. Each
    `label` is `0`.

    The resulting list of dictionaries is written to a `.csv` file, one file
    per document. The `.csv` file name consists of the original filename with
    `_sentences` appended. For example, `DoDM_1145.02_sentences.csv`.

    Returns:
        None
    """
    fname = None
    output_df = new_df()
    try:
        for sent_df, fname in raw2df(src_path, glob):
            output_df = output_df.append(sent_df, ignore_index=True)
            base, ext = os.path.splitext(os.path.basename(fname))
            output_csv = base.replace(" ", "_") + "_sentences" + ".csv"
            output_csv = os.path.join(output_path, output_csv)
            output_df.to_csv(output_csv, header=False, index=False)
            output_df = new_df()
    except (FileNotFoundError, IOError) as e:
        logger.exception("offending file : {}".format(fname))
        raise e


if __name__ == "__main__":
    from argparse import ArgumentParser

    import gamechangerml.src.text_classif.utils.log_init as li

    li.initialize_logger(to_file=False, log_name="none")

    fp = os.path.split(__file__)
    fp = "python " + fp[-1]
    parser = ArgumentParser(
        prog=fp,
        description="csv of each sentence in the text",
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
        "-o",
        "--output-csv",
        dest="output_csv",
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
    args = parser.parse_args()

    raw_text2csv(args.input_path, args.glob, args.output_csv)
