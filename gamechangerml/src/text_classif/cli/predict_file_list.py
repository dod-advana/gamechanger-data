"""
usage: python predict_file_list.py [-h] -m MODEL_PATH -d DOC_LIST -b
                                   BATCH_SIZE -l MAX_SEQ_LEN [--n N_SAMPLES]
                                   [-o OUTPUT_CSV] [--metrics]

predicts a list of files containing sentences

optional arguments:
  -h, --help            show this help message and exit
  -m MODEL_PATH, --model-path MODEL_PATH
                        directory of the torch model
  -d DOC_LIST, --doc-list DOC_LIST
                        text file with list of files to predict (.json)
  -b BATCH_SIZE, --batch-size BATCH_SIZE
                        batch size for the data samples
  -l MAX_SEQ_LEN, --max-seq-len MAX_SEQ_LEN
                        maximum sequence length, up to 512
  --n N_SAMPLES, --num-samples N_SAMPLES
                        if > 0, number of sequential samples to draw from the
                        data file
  -o OUTPUT_CSV, --output-csv OUTPUT_CSV
                        destination .csv file; optional
  --metrics             uses the label column in the input csv to compute/log
                        metrics
"""
import logging
import os

from gamechangerml.src.text_classif.cli.predict_cli import predict
from gamechangerml.src.text_classif.predictor import Predictor
from gamechangerml.src.text_classif.utils.log_init import initialize_logger

logger = logging.getLogger(__name__)


def predict_file_list(
    predictor,
    file_list,
    max_seq_len,
    batch_size,
    n_samples,
    metrics,
):
    for doc_file in file_list:
        doc_file = doc_file.strip()
        _, fname = os.path.split(doc_file)
        output_csv = fname.replace(".csv", "_predict.csv")
        predict(
            predictor,
            doc_file,
            max_seq_len,
            batch_size,
            n_samples,
            output_csv,
            metrics,
        )


if __name__ == "__main__":
    from argparse import ArgumentParser

    fp = os.path.split(__file__)
    fp = "python " + fp[-1]
    parser = ArgumentParser(
        prog=fp, description="predicts a list of files containing sentences"
    )
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
        "--doc-list",
        dest="doc_list",
        type=str,
        required=True,
        help="text file with list of files to predict (.json)",
    )
    parser.add_argument(
        "-b",
        "--batch-size",
        dest="batch_size",
        type=str,
        required=True,
        help="batch size for the data samples",
    )
    parser.add_argument(
        "-l",
        "--max-seq-len",
        dest="max_seq_len",
        type=int,
        required=True,
        help="maximum sequence length, up to 512",
    )
    parser.add_argument(
        "--n",
        "--num-samples",
        dest="n_samples",
        type=int,
        default=0,
        help="if > 0, number of sequential samples to draw from the data file",
    )
    parser.add_argument(
        "--metrics",
        dest="metrics",
        action="store_true",
        help="uses the label column in the input csv to compute/log metrics",
    )
    args = parser.parse_args()
    initialize_logger(to_file=False, log_name="none")

    with open(args.doc_list) as f:
        file_list_ = f.readlines()

    predictor_ = Predictor(args.model_path, num_labels=2)
    predict_file_list(
        predictor_,
        file_list_,
        args.max_seq_len,
        args.batch_size,
        args.n_samples,
        args.metrics,
    )
