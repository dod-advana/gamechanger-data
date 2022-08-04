"""
usage: python predict_cli.py [-h] -m MODEL_PATH -d DATA_PATH -b BATCH_SIZE -l
                             MAX_SEQ_LEN [--n N_SAMPLES] [-o OUTPUT_CSV]
                             [--metrics]

predicts a set of examples

optional arguments:
  -h, --help            show this help message and exit
  -m MODEL_PATH, --model-path MODEL_PATH
                        directory of the torch model
  -d DATA_PATH, --data-path DATA_PATH
                        path + file.csv, for input data .csv
  -b BATCH_SIZE, --batch-size BATCH_SIZE
                        batch size for the data samples
  -l MAX_SEQ_LEN, --max-seq-len MAX_SEQ_LEN
                        maximum sequence length, up to 512
  --n N_SAMPLES, --num-samples N_SAMPLES
                        if > 0, number of sequential samples to draw from the
                        data file
  -o OUTPUT_CSV, --output-csv OUTPUT_CSV
                        (optional) destination .csv file
  --metrics             uses the label column in the input csv to compute/log
                        metrics
"""
import logging
import os
import time

import numpy as np
import pandas as pd
from tqdm import tqdm

from gamechangerml.src.text_classif.predictor import Predictor
from gamechangerml.src.text_classif.utils.log_init import initialize_logger
import gamechangerml.src.text_classif.utils.classifier_utils as cu
import gamechangerml.src.text_classif.utils.metrics as m

logger = logging.getLogger(__name__)


def predict(
    predictor,
    data_file,
    max_seq_len,
    batch_size,
    n_samples,
    output_csv,
    metrics,
):
    """
    This example performs predictions using a checked-pointed model and a
    dataset. The various arguments are shown in `__main__`.

    The .csv  `data_file` is assumed to have a columns "src", "label", and
    "sentence". "label" can be all 0. For example, you may not have labeled
    data for a particular document.

    The `raw_text` of a document can be converted to a conforming .csv using
    `utils/raw_text2csv.py` in this package.

    If `metrics` is `True`, `label` is used as ground-truth. Metrics are
    logged. For sentences whose label is unknown, the label should be set
    to `0` and the `metrics` flag omitted.

    if `output_csv` is not `None`, the results will be written to this
    file.

    Returns:
        List[Dict]: Each entry will have all the columns in `data_file`
            prepended by columns `top_class`, `prob`. The new columns are the
            predicted class and the likelihood, as determined by the model.

    """
    if not os.path.isfile(data_file):
        msg = "not found: {}".format(data_file)
        logger.exception(msg)
        raise FileNotFoundError(msg)

    initialize_logger(to_file=False, log_name="none")

    out_list = list()
    input_dicts = cu.load_data(data_file, n_samples, shuffle=False)

    _, csv_name = os.path.split(data_file)
    logger.info("{:>35s} : {:,}".format(csv_name, len(input_dicts)))

    start = time.time()
    for output in tqdm(
        predictor.predict(
            input_dicts,
            batch_size=int(batch_size),
            max_seq_len=int(max_seq_len),
        ),
        desc="predict",
    ):
        out_list += output

    elapsed = time.time() - start
    rate = elapsed / len(out_list)
    logger.info("total seconds : {:>6.3f}".format(elapsed))
    logger.info("  secs / text : {:>6.3f}".format(rate))

    if metrics:
        y_true = np.array([v["label"] for v in out_list], dtype=np.int8)
        y_pred = np.array([v["top_class"] for v in out_list], dtype=np.int8)
        cm_matrix = m.cm_matrix(y_true, y_pred)
        mcc = m.mcc_val(y_true, y_pred)

        logger.info("confusion matrix\n\n\t{}\n".format(cm_matrix))
        logger.info("MCC : {:>0.3f}".format(mcc))

    if output_csv is not None:
        df = pd.DataFrame(data=out_list)
        df.to_csv(output_csv, header=True, index=False)
        logger.info("csv written to : {}".format(output_csv))
    return out_list


if __name__ == "__main__":
    from argparse import ArgumentParser

    parser = ArgumentParser(
        prog="python predict_cli.py", description="predicts a set of examples"
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
        "--data-path",
        dest="data_path",
        type=str,
        required=True,
        help="path + file.csv, for input data .csv",
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
        "-o",
        "--output-csv",
        dest="output_csv",
        type=str,
        default=None,
        help="destination .csv file; optional",
    )
    parser.add_argument(
        "--metrics",
        dest="metrics",
        action="store_true",
        help="uses the label column in the input csv to compute/log metrics",
    )
    args = parser.parse_args()
    predictor_ = Predictor(args.model_path, num_labels=2)
    predict(
        predictor_,
        args.data_path,
        args.batch_size,
        args.max_seq_len,
        args.n_samples,
        args.output_csv,
        args.metrics,
    )
