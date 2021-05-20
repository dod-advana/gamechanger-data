import logging
from time import time

from sklearn import metrics

logger = logging.getLogger(__name__)


def trim(s):
    return s if len(s) <= 80 else s[:77] + "..."


def sk_statistical(clf, x_train, y_train, y_test, x_test):
    """
    Run the classifier and collect results. This is intended for use with
    the `scikit-learn` classifiers. However, any classifier equipped with a
    `fit(x, y)` method and a `predict(x, y)` method can be used.

    Args:
        clf (callable): classifier object equipped with `fit(x, y)` method and
            a `predict(x, y)` method.

        x_train (np.array): training values

        y_train (np.array): training labels

        y_test (np.array):  test labels

        x_test (np.array):  test values


    Returns:
        str, float, float, float
    """
    logger.info("_" * 80)
    logger.info("Training: ")
    logger.info(clf)

    start = time()
    clf.fit(x_train, y_train)
    train_time = time() - start
    logger.info("{:>17s} : {:0.3f}s".format("train time", train_time))

    start = time()
    y_pred = clf.predict(x_test)
    test_time = time() - start
    logger.info("{:>17s} : {:0.3f}s".format("test time", test_time))

    score = metrics.accuracy_score(y_test, y_pred)
    logger.info("{:>17s} : {:0.3f}".format("accuracy", score))

    clf_descr = str(clf)
    return clf_descr, score, train_time, test_time, y_test, y_pred
