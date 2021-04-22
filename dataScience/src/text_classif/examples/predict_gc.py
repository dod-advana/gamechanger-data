"""
usage: predict_gc.py [-h] -c CONFIG_YAML -d DATA_FILE
                     [-m {bert,roberta,roberta-nd,distilbert}] -n NUM_SAMPLES
                     [-p MODEL_PATH]

Loads the checkpoint file and predicts labels for GC training data

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG_YAML, --config-yaml CONFIG_YAML
                        path to the `.yml` configuration file
  -d DATA_FILE, --data-file DATA_FILE
                        path the training data
  -m {bert,roberta,roberta-nd,distilbert}, --model-type {bert,roberta,roberta-nd,distilbert}
                        supported model type; default is `roberta'
  -n NUM_SAMPLES, --num-samples NUM_SAMPLES
                        number of random samples
  -p MODEL_PATH, --model-path MODEL_PATH
                        Optional. load the torch model from this directory
"""
import logging
import os

import pandas as pd

import dataScience.src.text_classif.utils.classifier_utils as cu
import dataScience.src.text_classif.utils.metrics as metrics
from dataScience.src.text_classif.roberta_classifier import RobertaClassifier
from dataScience.src.text_classif.distilbert_classifier import (
    DistilBertClassifier,
)
from dataScience.src.text_classif.utils.log_init import initialize_logger

logger = logging.getLogger(__name__)


def main(config_yaml, data_file, model_type, topn, model_path):
    """
    Example illustrating how to train the `roberta-base` model using the
    labeled GC data set.

    Args:
        model_path:
        config_yaml (str): path to the configuration file

        data_file (str): path to the data set

        model_type (str): one of
            ("bert", "roberta", "roberta-nd", "distilbert")

        topn (int): number of random samples for prediction

    Returns:
        None

    """
    if topn < 0:
        raise ValueError("topn must be >= 0, got {}".format(topn))

    here = os.path.dirname(os.path.realpath(__file__))

    # console logging only
    initialize_logger(to_file=False, log_name="discard", output_dir=here)

    # custom function to read / parse the GC data set
    dev_text, dev_labels, dev_src = cu.gc_data(
        data_file, None, shuffle=False, topn=topn
    )
    logger.info("num samples : {:,}".format(len(dev_labels)))

    try:
        if model_type == "roberta":
            clf = RobertaClassifier(config_yaml)
        elif model_type == "distilbert":
            clf = DistilBertClassifier(config_yaml)
        else:
            raise ValueError("unsupported model; got `{}`".format(model_type))
        if model_path is not None:
            clf.cfg.use_checkpoint_path = model_path
        elif clf.cfg.use_checkpoint is None:
            logger.error("no checkpoint to use for prediction")
            raise RuntimeError("no checkpoint to use for prediction")
        pred_labels = list()
        pred_probs = list()
        for labels, probs in clf.predict(dev_text.tolist()):
            pred_labels.extend(labels.tolist())
            pred_probs.extend(probs.tolist())

        clf_report = metrics.val_clf_report(dev_labels, pred_labels)
        cm_matrix = metrics.cm_matrix(dev_labels, pred_labels)
        mcc = metrics.mcc_val(dev_labels, pred_labels)
        logger.info("\n\n{}".format(clf_report))
        logger.info("confusion matrix\n\n\t{}\n".format(cm_matrix))
        logger.info("MCC : {:>0.3f}".format(mcc))

        output_df = pd.DataFrame(
            columns=["source", "predicted", "p", "text"]
        )
        for idx, sent in enumerate(dev_text):
            output_dict = {
                "source": dev_src[idx],
                "predicted": pred_labels[idx],
                "p": pred_probs[idx],
                "text": sent,
            }
            output_df = output_df.append(output_dict, ignore_index=True)
        return output_df
    except (FileNotFoundError, ValueError, AttributeError) as e:
        logger.fatal("{}: {}".format(type(e), str(e)), exc_info=True)
        raise e


if __name__ == "__main__":
    from argparse import ArgumentParser

    desc = "Loads the checkpoint file and predicts labels for GC training data"
    parser = ArgumentParser(prog="predict_gc.py", description=desc)
    parser.add_argument(
        "-c",
        "--config-yaml",
        required=True,
        type=str,
        dest="config_yaml",
        help="path to the `.yml` configuration file",
    )
    parser.add_argument(
        "-d",
        "--data-file",
        required=True,
        type=str,
        dest="data_file",
        help="path the training data",
    )
    parser.add_argument(
        "-m",
        "--model-type",
        choices=("bert", "roberta", "distilbert"),
        default=None,
        dest="model_type",
        help="supported model type; default is `None'",
    )
    parser.add_argument(
        "-n",
        "--num-samples",
        dest="num_samples",
        type=int,
        default=0,
        help="number of random samples",
    )
    parser.add_argument(
        "-p",
        "--model-path",
        dest="model_path",
        type=str,
        required=False,
        default=None,
        help="Optional. load the torch model from this directory"
    )

    args = parser.parse_args()

    out_df = main(args.config_yaml, args.data_file, args.model_type,
                  args.num_samples, args.model_path)
    out_df.to_csv("predict_gc.csv", header=True, index=False)
