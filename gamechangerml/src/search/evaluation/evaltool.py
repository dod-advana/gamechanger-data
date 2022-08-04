import os
import json
import logging
import mlflow

import matplotlib.pyplot as plt

import argparse

logger = logging.getLogger(__name__)


class EvalTool(object):
    """
    Object class that holds all functions for evaluating and
    plotting score metrics for ranked retrieval.

    The predictions are expected to come in this format:

    {
        "query_id_1": {
            "document_id_1": 1,
            "document_id_2": 2,
            "document_id_3": 3
        }
    }

    Args:
        prediction (string): File path of JSON or dictionary
                             containing the model predictions
        ground_truth (string): File path of JSON or dictionary
                               containing the ground truth
        k_s (list): List of values for k with which the model is
                    evaluated
        params (dict): Dictionary of parameters used for the model
    """

    def __init__(self, prediction, ground_truth, k_s=None, params=None):

        if os.path.isfile(prediction) and prediction.endswith("json"):
            self.prediction = self._load_json(prediction)
        else:
            raise FileNotFoundError("Prediction file was not found. Please make sure you are pointing to the correct JSON file...")

        if os.path.isfile(ground_truth) and ground_truth.endswith("json"):
            self.ground_truth = self._load_json(ground_truth)
        else:
            raise FileNotFoundError("Ground truth file was not found. Please makue sure you are point to the correct JSON file...")

        if k_s is None:
            self.k_s = [1] + [i * 5 for i in range(1, 21)]
        else:
            self.k_s = k_s

        self.params = params
        self.metrics_at_k = None

    def _load_json(self, json_path):
        """
        Load a JSON file

        Args:
            json_path (string): File path of JSON file to be loaded

        Returns:
            json_dict (dict): Dictionary of loaded JSON file
        """
        with open(json_path, "r") as fp:
            json_dict = json.load(fp)

        return json_dict

    def _score_prediction(self, predicted_ranking, relevant_documents):
        """
        Evaluate and retrieve scores from a ranked dictionary of predicted
        relevant documents and a list of relevant documents

        Args:
            predicted_ranking (dict): Dictionary containing document ids
                                      ranked based on relevance
            relevant_documents(list): List of documents ids that are considered
                                      relevant. Relevant documents are ranked
                                      as 1 regardless of their number

        Returns:
            precision (float): Precision score
            recall (float): Recall score
            best_rank (int): Best rank for any of the relevant documents
        """

        prediction_count = len(predicted_ranking)

        TP_count = 0
        FP_count = 0
        FN_count = 0

        best_rank = 1_000_000

        for relevant_doc in relevant_documents:
            if relevant_doc in predicted_ranking:
                TP_count += 1
                rank = predicted_ranking[relevant_doc]

                if best_rank > rank:
                    best_rank = rank
            else:
                FN_count += 1
        FP_count = prediction_count - TP_count

        precision = TP_count / (TP_count + FP_count)
        recall = TP_count / (TP_count + FN_count)

        return precision, recall, best_rank

    def _filter_predictions(self, predictions, k=100):
        """
        Filter predictions to only ones that are k or better.

        Args:
            predictions (dict): Dictionary containing document ids
                                ranked based on relevance
            k (int): Minimum rank for a prediction to be considered

        Returns:
            sub_predictions (dict): Dictionary containing document ids
                                    ranked based on relevance filtered
        """
        sub_predictions = {}

        for query_id, document_rank in predictions.items():
            subset_document_rank = {}

            for doc_id, rank in document_rank.items():
                if rank <= k:
                    subset_document_rank[doc_id] = rank

            sub_predictions[query_id] = subset_document_rank

        return sub_predictions

    def evaluate(self, get_plot=True):
        """
        Evaluates the entire prediction dictionary with the ground data.
        A `metrics.json` file is generated in the same directory as the
        prediction file. If `get_plot` is True, a graph of the precision,
        recall, and MRR is plotted and saved in the same directory.

        Args:
            get_plot (bool): If true, a graph is generated

        Returns:
            metrics_at_k (dict): Dictionary of k's and metrics at each k.
        """
        metrics_at_k = {}

        for k in self.k_s:
            subset_prediction = self._filter_predictions(self.prediction, k=k)
            precision_scores = []
            recall_scores = []
            best_ranks = []

            for query_id in self.prediction:
                if query_id in subset_prediction:
                    try:
                        prediction_ranks = subset_prediction[query_id]
                        relevant_docs = self.ground_truth[query_id]
                        precision, recall, best_rank = self._score_prediction(
                            prediction_ranks, relevant_docs
                        )
                    except:
                        pass
                else:
                    precision, recall, best_rank = 0.0, 0.0, 1_000_000

                precision_scores.append(precision)
                recall_scores.append(recall)
                best_ranks.append(best_rank)

            precision_at_k = sum(precision_scores) / len(precision_scores)
            recall_at_k = sum(recall_scores) / len(recall_scores)

            reciprocal_ranks = [1.0 / rank for rank in best_ranks]
            mrr_at_k = sum(reciprocal_ranks) / len(reciprocal_ranks)

            metrics_at_k[k] = {
                "precision": round(precision_at_k, 6),
                "recall": round(recall_at_k, 6),
                "mrr_at_k": round(mrr_at_k, 6),
            }

        self.metrics_at_k = metrics_at_k

        return metrics_at_k

    def plot_metrics(self, folder_path):
        """
        Save precision, recall, and MRR plots of the Evaluation

        Args:
            folder_path (str): Folder location where the results will be stored

        """

        # Precision
        precision_path = os.path.join(folder_path, "precision.png")
        plt.figure(figsize = (8,6))

        k_values = []
        precision_scores = []
        for k, scores in self.metrics_at_k.items():
            precision = scores["precision"]
            k_values.append(k)
            precision_scores.append(precision)
        
        plt.plot(k_values, precision_scores, label = "Precision")
        plt.xlabel("k values")
        plt.ylabel("Precision")
        plt.legend()
        plt.grid()
        plt.ylim(0, 1)
        plt.tight_layout()
        plt.savefig(precision_path)
        plt.clf()

        # Recall
        recall_path = os.path.join(folder_path, "recall.png")
        plt.figure(figsize = (8,6))

        k_values = []
        recall_scores = []
        for k, scores in self.metrics_at_k.items():
            recall = scores["recall"]
            k_values.append(k)
            recall_scores.append(recall)
        
        plt.plot(k_values, recall_scores, label = "Recall")
        plt.xlabel("k values")
        plt.ylabel("Recall")
        plt.legend()
        plt.grid()
        plt.ylim(0, 1)
        plt.tight_layout()
        plt.savefig(recall_path)
        plt.clf()

        # MRR
        mrr_path = os.path.join(folder_path, "mrr.png")
        plt.figure(figsize = (8,6))

        k_values = []
        mrr_scores = []
        for k, scores in self.metrics_at_k.items():
            mrr = scores["mrr_at_k"]
            k_values.append(k)
            mrr_scores.append(mrr)
        
        plt.plot(k_values, mrr_scores, label = "MRR")
        plt.xlabel("k values")
        plt.ylabel("MRR")
        plt.legend()
        plt.grid()
        plt.ylim(0, 1)
        plt.tight_layout()
        plt.savefig(mrr_path)
        plt.clf()

    def log_mflow(self, experiment_name="default", tracking_uri=None):
        """
        Log model parameters and metrics stored in EvalTool to an MLFlow
        server

        Args:
            experiment_name (str): Name of experiment to be stored
            tracking_uri (str): MLFlow server location where parameters
                                and metrics will be logged
        """

        # Connect to MLFlow Server
        if tracking_uri is not None:
            try:
                mlflow.set_tracking_uri(tracking_uri)
                logger.info(f"Connected to {tracking_uri}")
            except mlflow.exceptions.MlflowException as e:
                logger.error("Error accessing tracking uri")
                raise e

        # Create or connect to existing experiment
        try:
            mlflow_id = mlflow.create_experiment(name=experiment_name)
        except (
            mlflow.exceptions.RestException,
            mlflow.exceptions.MlflowException,
        ) as e:
            mlflow_id = mlflow.get_experiment_by_name(experiment_name).experiment_id
            logger.info(f"Experiment exists: {mlflow_id}")

        # Log parameters and metrics
        if self.metrics_at_k is None:
            logger.info("Nothing to log")
            return None

        metric_head = {}

        for k, value in self.metrics_at_k.items():
            for metric, score in value.items():
                metric_head[f"{metric}_at_{k}"] = value[metric]

        with mlflow.start_run(experiment_id=mlflow_id):
            mlflow.log_metrics(metric_head)

            if self.params is not None:
                mlflow.log_params(self.params)

        return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-p",
        "--prediction_path",
        dest="prediction_path",
        required=True,
        type=str,
        help="File path to JSON file with predictions of ranked retrieval",
    )
    parser.add_argument(
        "-g",
        "--ground_truth_path",
        dest="ground_truth_path",
        required=True,
        type=str,
        help="File path to JSON file with ground truth of ranked retrieval",
    )
    parser.add_argument(
        "-m",
        "--metrics-path",
        dest="metrics_path",
        required=True,
        type=str,
        help="Path to store metrics of evaluation to a JSON file",
    )
    args = parser.parse_args()

    ev = EvalTool(args.prediction_path, args.ground_truth_path)
    metrics = ev.evaluate()

    ev.plot_metrics(args.metrics_path)

    metrics_json = os.path.join(args.metrics_path, "metrics.json")
    with open(metrics_json, "w") as fp:
        json.dump(metrics, fp)
