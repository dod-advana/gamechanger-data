"""
usage: python predict_gc_doc.py

Loads the checkpoint file and predicts labels for GC data

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG_YAML, --config-yaml CONFIG_YAML
                        path to the `.yml` configuration file
  -d DATA_FILE, --data-file DATA_FILE
                        path the training data
  -m {bert,roberta,roberta-nd,distilbert}, --model-type {bert,roberta,roberta-nd,distilbert}
  -s SAMPLES, --samples SAMPLES
                        num random samples of out of domain data
"""
import logging
import os
import re

import dataScience.src.text_classif.utils.classifier_utils as cu
from dataScience.src.text_classif.distilbert_classifier import (
    DistilBertClassifier,
)  # noqa
from dataScience.src.text_classif.roberta_classifier_no_decay import (
    RobertaClassifier,
)  # noqa
from dataScience.src.text_classif.utils.log_init import initialize_logger
from dataScience.src.utilities.spacy_model import get_lg_vectors

logger = logging.getLogger(__name__)


def scrubber(text):
    text = re.sub("[\\n\\t\\r]+", " ", text)
    text = re.sub("\\s{2,}", " ", text)
    return text.strip()


def main(config_yaml, data_file, model_type):
    """
    Loads a checkpoint trained in one domain and uses the model to
    predict samples in another domain (transfer learning).

    Args:
        config_yaml (str): path to the configuration file

        data_file (str): path to the data set

        model_type (str): one of
            ("bert", "roberta", "roberta-nd", "distilbert")

    Returns:
        None

    """
    here = os.path.dirname(os.path.realpath(__file__))
    initialize_logger(
        to_file=False, log_name="test.discard.log", output_dir=here
    )

    try:
        if model_type in ("roberta", "roberta-nd"):
            clf = RobertaClassifier(config_yaml)
        elif model_type == "distilbert":
            clf = DistilBertClassifier(config_yaml)
        else:
            raise ValueError("unsupported model; got `{}`".format(model_type))
    except (FileNotFoundError, AttributeError, RuntimeError) as e:
        raise e

    logger.info("loading sentencizer")
    nlp = get_lg_vectors()
    nlp.add_pipe(nlp.create_pipe("sentencizer"))

    # custom function to read / parse the GC data set
    for raw_text, input_f in cu.gen_gc_docs(
        data_file, "DoDD 1401*.json", key="raw_text"
    ):
        sents = [scrubber(s.text) for s in nlp(raw_text).sents]
        logger.info("{:>20s} sentences : {:>4,d}".format(input_f, len(sents)))
        pred_labels = list()
        pred_probs = list()
        for labels, probs in clf.predict(sents):
            pred_labels.extend(labels)
            pred_probs.extend(probs)

        for idx, sent in enumerate(sents):
            logger.info(
                "{} : p={:0.3f}  {}".format(
                    pred_labels[idx], pred_probs[idx], sent
                )
            )


if __name__ == "__main__":
    import sys
    from argparse import ArgumentParser

    desc = "Loads the checkpoint file and predicts labels for GC data"
    parser = ArgumentParser(usage="python predict_gc_doc.py", description=desc)
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
        help="path to the JSON documents",
    )
    parser.add_argument(
        "-m",
        "--model-type",
        choices=("bert", "roberta", "roberta-nd", "distilbert"),
        required=True,
        dest="model_type",
        help="supported model type",
    )

    args = parser.parse_args()

    sys.exit(main(args.config_yaml, args.data_file, args.model_type))
