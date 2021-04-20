"""
usage: python example_cola_cli

Trains the `bert-based` models on the CoLA data set

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG_YAML, --config-yaml CONFIG_YAML
                        path to the `.yml` configuration file
  -d DATA_FILE, --data-file DATA_FILE
                        path the training data
  -m {bert, roberta, roberta-nd, bert-nd, distilbert},
                --model-type {bert, roberta, roberta-nd, bert-nd, distilbert}
                        supported model type; default is `roberta'
"""
import logging
import os

import dataScience.src.text_classif.utils.classifier_utils as cu
from dataScience.src.text_classif.bert_classifier import BertClassifier
from dataScience.src.text_classif.bert_classifier_no_decay import (
    BertClassifierNoDecay,
)  # noqa
from dataScience.src.text_classif.distilbert_classifier import (
    DistilBertClassifier,
)  # noqa
from dataScience.src.text_classif.roberta_classifier import RobertaClassifier
from dataScience.src.text_classif.roberta_classifier_no_decay import (
    RobertaClassifierNoDecay,
)  # noqa
from dataScience.src.text_classif.utils.log_init import initialize_logger

logger = logging.getLogger(__name__)


def main(config_yaml, data_file, model_type, trunc):
    """
    Example illustrating how to train the `roberta-base` model using the
    COLA data set.

    Args:
        config_yaml(str): path to the configuration file

        data_file(str): path to the data set

        model_type(str): one of
            ("bert", "bert-nd", "roberta", "roberta-nd", "distilbert")

        trunc(int): limit to this many samples; 0 means to use all samples

    Returns:
        None

    """
    here = os.path.dirname(os.path.realpath(__file__))

    try:
        if model_type == "roberta":
            clf = RobertaClassifier(config_yaml)
        elif model_type == "roberta-nd":
            clf = RobertaClassifierNoDecay(config_yaml)
        elif model_type == "bert":
            clf = BertClassifier(config_yaml)
        elif model_type == "bert-nd":
            clf = BertClassifierNoDecay(config_yaml)
        elif model_type == "distilbert":
            clf = DistilBertClassifier(config_yaml)
        else:
            raise ValueError("unsupported model; got `{}`".format(model_type))

        initialize_logger(
            to_file=True, log_name=clf.cfg.log_id, output_dir=here
        )
        # custom function to read / parse the CoLA data set
        train_sentences, train_labels = cu.cola_data(data_file)
        if trunc > 0:
            train_sentences = train_sentences[:trunc]
            train_labels = train_labels[:trunc]

        _ = clf.fit(train_sentences, train_labels)
    except (FileNotFoundError, ValueError, AttributeError) as e:
        logger.fatal("{}: {}".format(type(e), str(e)), exc_info=True)
        raise e


if __name__ == "__main__":
    import sys
    from argparse import ArgumentParser

    desc = "Trains the `bert-based` models on the CoLA data set"
    parser = ArgumentParser(usage="python example_cola_cli", description=desc)

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
        choices=("bert", "roberta", "roberta-nd", "bert-nd", "distilbert"),
        default="roberta",
        dest="model_type",
        help="supported model type; default is `roberta'",
    )
    parser.add_argument(
        "-t",
        "--truncate",
        type=int,
        default=0,
        dest="trunc",
        help="use rows up to this value; 0 indicates the entire data set",
    )

    args = parser.parse_args()

    sys.exit(
        main(args.config_yaml, args.data_file, args.model_type, args.trunc)
    )
