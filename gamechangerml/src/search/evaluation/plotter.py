import os
import json
import matplotlib.pyplot as plt

import logging
import argparse

logger = logging.getLogger(__name__)

def load_json(path):
    """
    Load json file

    Args:
        path (str): Path to JSON file
    
    Returns:
        data (dict): Dictionary form of JSON file
    """
    with open(path, "r") as fp:
        data = json.load(fp)
    return data


def load_all_metrics(data_path):
    """
    Load all `metrics.json` files in a directory.

    Args:
        data_path (str): Path of folder directory containing all tests

    Returns:
        all_data (dict): Dictionary form containing all data of all metrics
    """
    all_data = {}

    for root, dirs, files in os.walk(data_path, topdown=True):
        for name in files:
            if name == "metrics.json":
                file_path = os.path.join(root, name)
                model_name = root.split("/")[-1]

                all_data[model_name] = load_json(file_path)

    return all_data


def generate_report(all_data, fname, metric):
    """
    Generate a report from all_data given a 
    specific metric

    Args:
        all_data (dict): Dictionary of all metrics from a directory
                         containing all of the tests
        fname (str): Filename to save the report graph
        metric (str): Metric name to evaluate in the metrics file
    """
    plt.figure(figsize=(8, 6))

    for model_name, data in all_data.items():
        k_s = []
        score = []
        for key, value in data.items():
            k_s.append(key)
            score.append(value[metric])

        plt.plot(k_s, score, label=model_name, marker=".")

    plt.ylabel(metric.title())
    plt.xlabel("k")
    plt.title(f"{metric.title()} Scores")
    plt.ylim((0.0, 1.0))
    plt.grid()
    plt.legend()

    plt.savefig(fname)


def generate_mrr(all_data, fname):
    """
    Generate an MRR report from all_data

    Args:
        all_data (dict): Dictionary of all metrics from a directory
                         containing all of the tests
        fname (str): Filename to save the report graph
    """
    plt.figure(figsize=(8, 4))

    models = []
    scores = []
    for model_name, data in sorted(all_data.items(), reverse = True):
        models.append(model_name)
        scores.append(data["10"]["mrr_at_k"])

    plt.title("MRR Scores at k=10")
    plt.xlim((0.0, 1.0))
    plt.barh(range(len(scores)), scores)
    plt.yticks(range(len(models)), models)

    for model_name, score in zip(models, scores):
        plt.annotate(round(score, 3), (score, models.index(model_name)-0.2))

    plt.tight_layout()
    plt.savefig(fname)
    
def generate_precision_recall(all_data, fname):
    """
    Generate an precision and recall report from all_data

    Args:
        all_data (dict): Dictionary of all metrics from a directory
                         containing all of the tests
        fname (str): Filename to save the report graph
    """
    plt.figure(figsize=(8,6))

    models = []
    precision_list = []
    recall_list = []
    for model_name, data in all_data.items():
        models.append(model_name)
        precision = []
        recall = []
        for key, value in data.items():
            precision.append(value['precision'])
            recall.append(value['recall'])
        precision_list.append(precision)
        recall_list.append(recall)
        plt.plot(precision, recall, label = model_name)
    
    plt.ylim(0, 1)
    plt.xlim(0, 1)
    plt.xlabel("Recall")
    plt.ylabel("Precision")
    plt.legend()

    plt.grid()
    plt.tight_layout()
    plt.savefig(fname)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-e",
        "--eval_path",
        dest="evaluation_path",
        required=True,
        type=str,
        help="Folder path to model predictions that have been evaluated",
    )

    args = parser.parse_args()
    path = args.evaluation_path

    all_data = load_all_metrics(path)
    fname = f"{path}/precision.png"
    generate_report(all_data, fname, "precision")
    fname = f"{path}/recall.png"
    generate_report(all_data, fname, "recall")
    fname = f"{path}/mrr_line.png"
    generate_report(all_data, fname, "mrr_at_k")
    fname = f"{path}/mrr.png"
    generate_mrr(all_data, fname)
    fname = f"{path}/precision_recall.png"
    generate_precision_recall(all_data, fname)
