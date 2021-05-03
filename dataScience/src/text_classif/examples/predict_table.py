"""
usage: python predict_table.py [-h] -m MODEL_PATH -d DATA_PATH [-b BATCH_SIZE]
                              [-l MAX_SEQ_LEN] -g GLOB [-o OUTPUT_CSV]

Binary classification of each sentence in the files matching the 'glob' in
data_path

optional arguments:
  -h, --help            show this help message and exit
  -m MODEL_PATH, --model-path MODEL_PATH
                        directory of the torch model
  -d DATA_PATH, --data-path DATA_PATH
                        path holding the .json corpus files
  -b BATCH_SIZE, --batch-size BATCH_SIZE
                        batch size for the data samples; default=8
  -l MAX_SEQ_LEN, --max-seq-len MAX_SEQ_LEN
                        maximum sequence length, 128 to 512; default=128
  -g GLOB, --glob GLOB  file glob pattern
  -o OUTPUT_CSV, --output-csv OUTPUT_CSV
                        the .csv for output
"""
import logging
import time
from argparse import ArgumentParser

import dataScience.src.text_classif.utils.classifier_utils as cu
from dataScience.src.text_classif.utils.entity_coref import EntityCoref
from dataScience.src.text_classif.utils.log_init import initialize_logger

logger = logging.getLogger(__name__)


if __name__ == "__main__":

    desc = "Binary classification of each sentence in the files "
    desc += "matching the 'glob' in data_path"
    parser = ArgumentParser(prog="python predict_table.py", description=desc)
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
        help="batch size for the data samples; default=8",
    )
    parser.add_argument(
        "-l",
        "--max-seq-len",
        dest="max_seq_len",
        type=int,
        default=128,
        help="maximum sequence length, 128 to 512; default=128",
    )
    parser.add_argument(
        "-g",
        "--glob",
        dest="glob",
        type=str,
        required=True,
        help="file glob pattern",
    )
    parser.add_argument(
        "-o",
        "--output-csv",
        dest="output_csv",
        type=str,
        default=None,
        help="the .csv for output",
    )

    initialize_logger(to_file=False, log_name="none")

    args = parser.parse_args()

    start = time.time()
    entity_coref = EntityCoref()
    _ = entity_coref.make_table(
        args.model_path,
        args.data_path,
        args.glob,
        args.max_seq_len,
        args.batch_size,
        args.output_csv,
    )
    elapsed = time.time() - start

    logger.info("total time : {:}".format(cu.format_time(elapsed)))
