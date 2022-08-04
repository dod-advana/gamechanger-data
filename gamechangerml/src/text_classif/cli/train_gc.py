"""
usage: example_gc_cli.py [-h] -c CONFIG_YAML -d DATA_FILE -m
                         {bert,roberta,distilbert} [-n NUM_SAMPLES]
                         [-k CHECKPOINT_PATH]

Trains the `bert-based` models on the gamechanger data set

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG_YAML, --config-yaml CONFIG_YAML
                        path to the `.yml` configuration file
  -d DATA_FILE, --data-file DATA_FILE
                        path the training data
  -m {bert,roberta,distilbert}, --model-type {bert,roberta,distilbert}
                        supported model type
  -n NUM_SAMPLES, --num-samples NUM_SAMPLES
                        if > 0, use this many samples for training
  -k CHECKPOINT_PATH, --checkpoint-path CHECKPOINT_PATH
                        directory to write each epoch's checkpoint files

"""
import logging
import os

import gamechangerml.src.text_classif.utils.classifier_utils as cu
from gamechangerml.src.text_classif.bert_classifier import BertClassifier
from gamechangerml.src.text_classif.distilbert_classifier import (
    DistilBertClassifier,
)
from gamechangerml.src.text_classif.roberta_classifier import RobertaClassifier
from gamechangerml.src.text_classif.utils.log_init import initialize_logger

logger = logging.getLogger(__name__)


def train_gc(config_yaml, data_file, model_type, num_samples, checkpoint_path):
    """
    Example illustrating how to train the classifier model.

    Args:
        config_yaml (str): path to the configuration file

        data_file (str): path to the data set

        model_type (str): one of ("bert", "roberta", "distilbert")

        num_samples (int): path where additional negative samples can
            be read and used to balance the classes

        checkpoint_path (str): if not None, subdirectories of this directory
            will contain a checkpoint for each epoch. The subdirectory name is
            `checkpoint_path_epoch_1`, etc.

    Returns:
        dict of runtime stats

    """
    here = os.path.dirname(os.path.realpath(__file__))
    try:
        if model_type == "roberta":
            clf = RobertaClassifier(config_yaml)
        elif model_type == "bert":
            clf = BertClassifier(config_yaml)
        elif model_type == "distilbert":
            clf = DistilBertClassifier(config_yaml)
        else:
            raise ValueError("unsupported model; got `{}`".format(model_type))

        clf.cfg.checkpoint_path = checkpoint_path

        initialize_logger(
            to_file=True, log_name=clf.cfg.log_id, output_dir=here
        )
        train_txt, train_labels, _ = cu.gc_data(
            data_file, None, shuffle=True, topn=num_samples
        )
        _, data_name = os.path.split(data_file)

        # `runtime` is a dictionary where various runtime parameters can be
        # stored.
        clf.runtime["training data"] = data_name

        # train on all samples
        rs = clf.fit(train_txt, train_labels)
        return rs
    except (FileNotFoundError, ValueError, AttributeError) as e:
        logger.fatal("{}: {}".format(type(e), str(e)), exc_info=False)
        raise e


if __name__ == "__main__":
    import sys
    from argparse import ArgumentParser

    desc = "Trains the `bert-based` models on the gamechanger data set"
    parser = ArgumentParser(prog="example_gc_cli.py", description=desc)

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
        required=True,
        dest="model_type",
        help="supported model type",
    )
    parser.add_argument(
        "-n",
        "--num-samples",
        type=int,
        dest="num_samples",
        default=0,
        help="if > 0, use this many samples for training",
    )
    parser.add_argument(
        "-k",
        "--checkpoint-path",
        type=str,
        dest="checkpoint_path",
        default=None,
        help="directory to write each epoch's checkpoint files",
    )

    args = parser.parse_args()

    sys.exit(
        train_gc(
            args.config_yaml,
            args.data_file,
            args.model_type,
            args.num_samples,
            args.checkpoint_path,
        )
    )
