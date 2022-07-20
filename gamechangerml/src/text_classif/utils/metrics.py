# The MIT License (MIT)
# Subject to the terms and conditions in LICENSE
import numpy as np
import pandas as pd
from sklearn import metrics

from gamechangerml.src.text_classif.utils.classifier_utils import (
    flatten_labels,
)


def logit_score(logits):
    score = np.max(logits, axis=1).flatten()
    return score.tolist()


def auc_val(y_true, y_logits, binary_classif=True):
    auc = metrics.roc_auc_score(y_true, y_logits, multi_class="raise" if binary_classif else "ovr")
    return auc


def flat_accuracy(preds, labels):
    pred_flat, labels_flat = flatten_labels(preds, labels)
    return np.sum(pred_flat == labels_flat) / len(labels_flat)


def accuracy_score(y_true, y_pred):
    return metrics.accuracy_score(y_true, y_pred)


def val_clf_report(y_true, y_pred):
    clf_report = metrics.classification_report(y_true, y_pred, digits=3)
    return clf_report


def mcc_val(y_true, y_pred):
    return metrics.matthews_corrcoef(y_true, y_pred)


def cm_matrix(y_true, y_pred):
    unique_label = np.unique([y_true, y_pred])
    cm_pd = pd.DataFrame(
        metrics.confusion_matrix(y_true, y_pred, labels=unique_label),
        index=["true: {:}".format(x) for x in unique_label],
        columns=["pred: {:}".format(x) for x in unique_label],
    )
    return cm_pd
