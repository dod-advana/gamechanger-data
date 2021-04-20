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
                        supported model type; default is `roberta'
  -s SAMPLES, --samples SAMPLES
                        num random samples of out of domain data
"""
import logging
import os

import pandas as pd

import dataScience.src.text_classif.utils.classifier_utils as cu
import dataScience.src.text_classif.utils.metrics as metrics
from dataScience.src.text_classif.distilbert_classifier import (
    DistilBertClassifier,
)
from dataScience.src.text_classif.roberta_classifier_no_decay import (
    RobertaClassifier,
)
from dataScience.src.text_classif.utils.log_init import initialize_logger

logger = logging.getLogger(__name__)
here = os.path.dirname(os.path.realpath(__file__))


def main(config_yaml, data_file, model_type, samples):
    """
    Loads a checkpoint trained in one domain and uses the model to
    predict samples in another domain (transfer learning).

    Args:
        config_yaml (str): path to the configuration file

        data_file (str): path to the data set

        model_type (str): one of ("bert", "roberta", "roberta-nd", "distilbert")

        samples (int): number of random samples to predict from `data_file`

    Returns:
        None

    """

    # custom function to read / parse the GC data set
    dev_sents, dev_labels, dev_src = cu.gc_data(
        data_file, None, shuffle=True, topn=samples
    )
    logger.info("num samples : {:,}".format(len(dev_labels)))

    # dev_sents = dev_sents[:samples]
    # dev_labels = dev_labels[:samples]
    # dev_src = dev_src[:samples]

    data_name = "predict-" + model_type + ".log"
    initialize_logger(to_file=True, log_name=data_name, output_dir=here)
    try:
        if model_type in ("roberta", "roberta-nd"):
            clf = RobertaClassifier(config_yaml)
        elif model_type == "distilbert":
            clf = DistilBertClassifier(config_yaml)
        else:
            raise ValueError("unsupported model; got `{}`".format(model_type))

        pred_labels = list()
        pred_probs = list()
        for labels, probs in clf.predict(dev_sents.tolist()):
            pred_labels.extend(labels.tolist())
            pred_probs.extend(probs.tolist())

        clf_report = metrics.val_clf_report(dev_labels, pred_labels)
        cm_matrix = metrics.cm_matrix(dev_labels, pred_labels)
        mcc = metrics.mcc_val(dev_labels, pred_labels)

        logger.info("\n\n{}".format(clf_report))
        logger.info("confusion matrix\n\n\t{}\n".format(cm_matrix))
        logger.info("\tMCC : {:>0.3f}".format(mcc))

        output_df = pd.DataFrame(
            columns=["source", "predicted", "p", "actual", "text"]
        )
        for idx, sent in enumerate(dev_sents):
            output_dict = {
                "source": dev_src[idx],
                "predicted": pred_labels[idx],
                "p": pred_probs[idx],
                "actual": dev_labels[idx],
                "text": sent,
            }
            output_df = output_df.append(output_dict, ignore_index=True)
            logger.debug(
                "label {} (p={:0.3f}) (actual {}), {}".format(
                    pred_labels[idx], pred_probs[idx], dev_labels[idx], sent
                )
            )
        output_df = output_df.sort_values(by="source")
        return output_df
    except (FileNotFoundError, ValueError, AttributeError) as e:
        logger.fatal("{}: {}".format(type(e), str(e)), exc_info=True)
        raise e


if __name__ == "__main__":
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
    parser.add_argument(
        "-s",
        "--samples",
        dest="samples",
        default=64,
        type=int,
        help="num random samples of out of domain data",
    )
    parser.add_argument(
        "-o",
        "--csv-output-name",
        dest="csv_output_name",
        default=None,
        type=str,
        help="writes the results to the named csv file",
    )

    args = parser.parse_args()

    out_df = main(
        args.config_yaml, args.data_file, args.model_type, args.samples
    )

    if args.csv_output_name is not None:
        out_df.to_csv(args.csv_output_name, sep=",", index=False)
