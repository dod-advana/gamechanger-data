"""
usage: python example_load_checkpoint.py

Loads the checkpoint file and predicts labels

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG_YAML, --config-yaml CONFIG_YAML
                        path to the `.yml` configuration file
  -d DATA_FILE, --data-file DATA_FILE
                        path the training data
  -m {bert,roberta,roberta-nd,distilbert}, --model-type {bert,roberta,roberta-nd,distilbert}
                        supported model type; default is `roberta'
"""
import logging
import os
import pandas as pd
from transformers import DistilBertForSequenceClassification
from transformers import DistilBertTokenizer

import dataScience.src.text_classif.utils.classifier_utils as cu
import dataScience.src.text_classif.utils.metrics as metrics
from dataScience.src.text_classif.distilbert_classifier import (
    DistilBertClassifier,
)  # noqa
from dataScience.src.text_classif.utils.log_init import initialize_logger

logger = logging.getLogger(__name__)


def main(config_yaml, data_file, model_type):
    """
    Example illustrating how to train the `roberta-base` model using the
    COLA data set.

    Args:
        config_yaml (str): path to the configuration file

        data_file (str): path to the data set

        model_type (str): one of ("bert", "roberta", "roberta-nd", "distilbert")

    Returns:
        None

    """
    data_name = model_type + "-cola-cli-example-predict_ex.log"
    here = os.path.dirname(os.path.realpath(__file__))
    initialize_logger(to_file=True, log_name=data_name, output_dir=here)

    # custom function to read / parse the GC data set
    dev_sentences, dev_labels = cu.cola_data(data_file)
    dev_sentences = dev_sentences[:64]
    dev_labels = dev_labels[:64]
    logger.info("num sentences : {:,}".format(len(dev_labels)))

    try:
        if model_type == "distilbert":
            model_class = DistilBertForSequenceClassification
            tokenizer_class = DistilBertTokenizer
            clf = DistilBertClassifier(config_yaml)
        else:
            raise ValueError("unsupported model; got `{}`".format(model_type))

        clf.model, clf.tokenizer = clf.load_checkpoint(
            model_class, tokenizer_class
        )
        logger.info("model loaded : {}".format(str(clf.model)))

        pred_labels = list()
        pred_probs = list()
        for labels, probs in clf.predict(dev_sentences.tolist()):
            pred_labels.extend(labels.tolist())
            pred_probs.extend(probs.tolist())

        clf_report = metrics.val_clf_report(dev_labels, pred_labels)
        cm_matrix = metrics.cm_matrix(dev_labels, pred_labels)
        mcc = metrics.mcc_val(dev_labels, pred_labels)

        logger.info("\n\n{}".format(clf_report))
        logger.info("confusion matrix\n\n\t{}\n".format(cm_matrix))
        logger.info("\t            MCC : {:>0.3f}".format(mcc))

        output_df = pd.DataFrame(
            columns=["source", "predicted", "p", "actual", "text"]
        )
        for idx, sent in enumerate(dev_sentences):
            output_dict = {
                "predicted": pred_labels[idx],
                "p": pred_probs[idx],
                "actual": dev_labels[idx],
                "text": sent,
            }
            output_df = output_df.append(output_dict, ignore_index=True)
            logger.info(
                "label {} (p={:0.3f}) (actual {}), {}".format(
                    pred_labels[idx], pred_probs[idx], dev_labels[idx], sent
                )
            )
        out_path = os.path.join(here, "cola-test-predict.csv")
        output_df.to_csv(out_path, sep=",", index=False)
    except (FileNotFoundError, ValueError, AttributeError) as e:
        logger.fatal("{}: {}".format(type(e), str(e)), exc_info=True)
        raise e


if __name__ == "__main__":
    import sys
    from argparse import ArgumentParser

    desc = "Loads the checkpoint file and predicts labels for GC data"
    parser = ArgumentParser(usage="python predict_gc.py", description=desc)
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
        choices=("bert", "roberta", "roberta-nd", "distilbert"),
        default="roberta",
        dest="model_type",
        help="supported model type; default is `roberta'",
    )

    args = parser.parse_args()

    sys.exit(main(args.config_yaml, args.data_file, args.model_type))
