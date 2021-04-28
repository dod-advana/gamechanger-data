"""
usage: python predict_glob.py [-h] -m MODEL_PATH -d DATA_PATH [-b BATCH_SIZE]
                              [-l MAX_SEQ_LEN] -g GLOB

Binary classification of each sentence in the files matching the 'glob'

optional arguments:
  -h, --help            show this help message and exit
  -m MODEL_PATH, --model-path MODEL_PATH
                        directory of the torch model
  -d DATA_PATH, --data-path DATA_PATH
                        path holding the .json corpus files
  -b BATCH_SIZE, --batch-size BATCH_SIZE
                        batch size for the data samples
  -l MAX_SEQ_LEN, --max-seq-len MAX_SEQ_LEN
                        maximum sequence length, 128 to 512
  -g GLOB, --glob GLOB  file glob pattern
"""
import logging
import os
import time

from tqdm import tqdm

import dataScience.src.text_classif.utils.classifier_utils as cu
import dataScience.src.utilities.spacy_model as spacy_m
from dataScience.src.text_classif.predictor import Predictor
from dataScience.src.text_classif.utils.log_init import initialize_logger

logger = logging.getLogger(__name__)


def _predict_docs(input_dicts, predictor, max_seq_len=128, batch_size=8):
    adder = 0
    if len(input_dicts) % batch_size != 0:
        adder = 1
    batches = len(input_dicts) // batch_size + adder
    out_list = list()
    start = time.time()
    for output in tqdm(
        predictor.predict(
            input_dicts,
            batch_size=int(batch_size),
            max_seq_len=int(max_seq_len),
        ),
        desc="predict",
        total=batches,
    ):
        out_list.extend(output)

    elapsed = time.time() - start
    rate = elapsed / len(out_list)
    logger.info("total seconds : {:}".format(cu.format_time(elapsed)))
    logger.info(" time / text : {:>6.3f} secs".format(rate))
    return out_list


def predict_glob(
    model_path_name,
    data_path,
    glob,
    max_seq_len=128,
    batch_size=8,
):
    """
    This performs classification on .json corpus docs using `raw_text`. The
    text is passed through the spaCy "sentencizer" to create a list of
    dictionaries, one for each extracted sentence.

    Batches(`batch_size`) of these dictionaries are sent forward through the
    model(`model_name_path`) with the predicted class and p(class) assembled
    in a dictionary and yielded.

    Args:
        model_path_name (str): path of the checkpointed model

        data_path (str): path containing the .json corpus files

        glob (str): file pattern to match, e.g., DoDD*.json

        max_seq_len (int): max number of tokens after encoding; default=128

        batch_size (int): batch size

    Yields:
        List[Dict]

    """
    if not os.path.isdir(data_path):
        raise ValueError("no directory named '{}'".format(data_path))
    if not 128 <= max_seq_len <= 512:
        raise ValueError("invalid max_seq_len; got {}".format(max_seq_len))
    if batch_size < 8:
        raise ValueError("invalid batch_size; got {}".format(batch_size))
    if not glob.strip():
        raise ValueError("invalid file glob; got '{}'".format(glob))
    if not os.path.isfile(os.path.join(model_path_name, "config.json")):
        raise FileNotFoundError("model_path_dir has no model")

    initialize_logger(to_file=False, log_name="none")
    logger.info("loading spaCY")

    predictor = Predictor(model_path_name, num_labels=2)

    nlp = spacy_m.get_lg_vectors()
    nlp.add_pipe(nlp.create_pipe("sentencizer"))

    for input_dicts, fname in cu.raw2dict(
        data_path, glob, nlp, key="raw_text"
    ):
        out_list = _predict_docs(
            input_dicts, predictor, max_seq_len, batch_size
        )
        yield out_list, fname


# CLI example
if __name__ == "__main__":
    from argparse import ArgumentParser

    desc = "Binary classification of each sentence in the files "
    desc += "matching the 'glob'"
    parser = ArgumentParser(prog="python predict_glob.py", description=desc)
    parser.add_argument(
        "-m",
        "--model-path",
        dest="model_path",
        type=str,
        required=True,
        help="directory of the torch model",
    )
    parser.add_argument(
        "-d",
        "--data-path",
        dest="data_path",
        type=str,
        required=True,
        help="path holding the .json corpus files",
    )
    parser.add_argument(
        "-b",
        "--batch-size",
        dest="batch_size",
        type=int,
        default=8,
        help="batch size for the data samples",
    )
    parser.add_argument(
        "-l",
        "--max-seq-len",
        dest="max_seq_len",
        type=int,
        default=128,
        help="maximum sequence length, 128 to 512",
    )
    parser.add_argument(
        "-g",
        "--glob",
        dest="glob",
        type=str,
        required=True,
        help="file glob pattern",
    )
    args = parser.parse_args()
    for output_list, file_name in predict_glob(
        args.model_path,
        args.data_path,
        args.glob,
        args.max_seq_len,
        args.batch_size,
    ):
        logger.info("processed : {:,}".format(len(output_list)))
