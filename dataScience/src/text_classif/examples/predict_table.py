"""
usage: python predict_table.py [-h] -m MODEL_PATH -d DATA_PATH [-b BATCH_SIZE]
                              [-l MAX_SEQ_LEN] -g GLOB

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
"""

import dataScience.src.utilities.spacy_model as spacy_m
from dataScience.src.text_classif.utils.log_init import initialize_logger
from dataScience.src.text_classif.utils.predict_glob import predict_glob


def _resolve_entity(output_list):
    return output_list


def make_table(
    model_path,
    data_path,
    glob,
    max_seq_len,
    batch_size,
    nlp,
):
    # a list entry looks like:
    #
    # {'top_class': 0, 'prob': 0.997, 'src': 'DoDD 5105.21.json', 'label': 0,
    #  'sentence': 'Department of...'}
    #
    # `top_class` is the predicted label
    for output_list, file_name in predict_glob(
        model_path,
        data_path,
        glob,
        max_seq_len,
        batch_size,
        nlp=nlp,
    ):
        output = _resolve_entity(output_list)
        logger.info("processed : {:,}  {}".format(len(output), file_name))


# CLI example
if __name__ == "__main__":
    import logging
    from argparse import ArgumentParser

    logger = logging.getLogger(__name__)

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

    initialize_logger(to_file=False, log_name="none")

    args = parser.parse_args()

    logger.info("loading spaCy")
    nlp_ = spacy_m.get_lg_vectors()

    # must always add the pipeline component "sentencizer"
    nlp_.add_pipe(nlp_.create_pipe("sentencizer"))

    make_table(
        args.model_path,
        args.data_path,
        args.glob,
        args.max_seq_len,
        args.batch_size,
        nlp=nlp_,
    )
