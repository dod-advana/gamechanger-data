import logging
import numpy as np

from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import SelectFromModel
from sklearn.linear_model import PassiveAggressiveClassifier
from sklearn.linear_model import Perceptron
from sklearn.linear_model import RidgeClassifier
from sklearn.linear_model import SGDClassifier
from sklearn.naive_bayes import BernoulliNB, ComplementNB, MultinomialNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neighbors import NearestCentroid
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

from dataScience.experimental.policy.text_classif.utils.benchmarks import (
    sk_statistical,
)

logger = logging.getLogger(__name__)


def run_shotgun_clf(X_train, y_train, y_test, X_test):
    """
    Runs all the classifiers in `sklearn`. Taken from scikit-learn docs.

    Args:
        X_train (np.array): training values

        y_train (np.array): training labels

        y_test (np.array):  test labels

        X_test (np.array):  test values


    Returns:

    """
    results = list()
    for clf, name in (
        (RidgeClassifier(tol=1e-2, solver="sag"), "Ridge Classifier"),
        (Perceptron(max_iter=50), "Perceptron"),
        (PassiveAggressiveClassifier(max_iter=50), "Passive-Aggressive"),
        (KNeighborsClassifier(n_neighbors=10), "kNN"),
        (RandomForestClassifier(), "Random forest"),
    ):
        logger.info("=" * 80)
        logger.info(name)
        results.append(sk_statistical(clf, X_train, y_train, y_test, X_test))

    for penalty in ["l2", "l1"]:
        logger.info("=" * 80)
        logger.info("{} penalty".format(penalty.upper()))

        # Train Liblinear model
        results.append(
            sk_statistical(
                LinearSVC(penalty=penalty, dual=False, tol=1e-3),
                X_train,
                y_train,
                y_test,
                X_test,
            )
        )

        # Train SGD model
        results.append(
            sk_statistical(
                SGDClassifier(alpha=0.0001, max_iter=50, penalty=penalty),
                X_train,
                y_train,
                y_test,
                X_test,
            )
        )

    # Train SGD with Elastic Net penalty
    logger.info("=" * 80)
    logger.info("Elastic-Net penalty")
    results.append(
        sk_statistical(
            SGDClassifier(alpha=0.0001, max_iter=50, penalty="elasticnet"),
            X_train,
            y_train,
            y_test,
            X_test,
        )
    )

    # Train NearestCentroid without threshold
    logger.info("=" * 80)
    logger.info("NearestCentroid (aka Rocchio classifier)")
    results.append(
        sk_statistical(NearestCentroid(), X_train, y_train, y_test, X_test)
    )

    # Train sparse Naive Bayes classifiers
    logger.info("=" * 80)
    logger.info("Naive Bayes")
    results.append(
        sk_statistical(
            MultinomialNB(alpha=0.01), X_train, y_train, y_test, X_test
        )
    )
    results.append(
        sk_statistical(
            BernoulliNB(alpha=0.01), X_train, y_train, y_test, X_test
        )
    )
    results.append(
        sk_statistical(
            ComplementNB(alpha=0.1), X_train, y_train, y_test, X_test
        )
    )

    logger.info("=" * 80)
    logger.info("LinearSVC with L1-based feature selection")

    # The smaller C, the stronger the regularization.
    # The more regularization, the more sparsity.
    results.append(
        sk_statistical(
            Pipeline(
                [
                    (
                        "feature_selection",
                        SelectFromModel(
                            LinearSVC(penalty="l1", dual=False, tol=1e-3)
                        ),
                    ),
                    ("classification", LinearSVC(penalty="l2")),
                ]
            ),
            X_train,
            y_train,
            y_test,
            X_test,
        )
    )
    best_statistical = np.argmax([r[1] for r in results])
    logger.info(
        "'best' classifier : {}  acc = {:0.4f}".format(
            results[best_statistical][0], results[best_statistical][1]
        )
    )
    return results
