import logging
import os

from sklearn.linear_model import SGDClassifier

from dataScience.experimental.policy.text_classif.classsifier import TextClf
from dataScience.experimental.policy.text_classif.utils.benchmarks import (
    sk_statistical,
)
from dataScience.experimental.policy.text_classif.utils.config import Config
from dataScience.experimental.policy.text_classif.utils.data_loader import (
    load_cola,
)
from dataScience.experimental.policy.text_classif.utils.extract_features_bow import (  # noqa
    extract_features_bow,
)
from dataScience.experimental.policy.text_classif.utils.log_init import (
    initialize_logger,
)
from dataScience.experimental.policy.text_classif.utils.path_to_config_dir import (  # noqa
    to_config_dir,
)

logger = logging.getLogger(__name__)


def exc_sgd(data_name="no name", cfg=None):
    """
    Run SGDClassifier on the CoLA data set.

    Args:
        data_name (str): user-supplied name

        cfg (Configuration): see `utils/config.py`, and `main()`

    Returns:
        None

    """
    logger.info(data_name)
    clf = SGDClassifier(alpha=0.0001, max_iter=50, penalty="elasticnet")

    x_train, y_train, x_test, y_test = load_cola()

    X_test, X_train, feat_names = extract_features_bow(
        x_train,
        x_test,
        sublinear=cfg.sublinear,
        max_df=float(cfg.max_df),
        min_df=int(cfg.min_df),
    )

    results = sk_statistical(clf, X_train, y_train, y_test, X_test)

    return results


if __name__ == "__main__":

    # The main show

    dn = "SGD COLA data set"
    dnh = dn.replace(" ", "-")
    target_names_ = ["NG", "G"]  # not grammatical, grammatical

    initialize_logger(to_file=False, data_name=dnh)

    path_to_config = os.path.join(to_config_dir(), "sgd_cola_config.json")
    assert os.path.isfile(path_to_config)

    cfg_ = Config(config_file=path_to_config)
    cfg_.add("target_names", target_names_)

    text_clf = TextClf()
    text_clf.fit(fit_func=exc_sgd, data_name=dn, cfg=cfg_)

    report = text_clf.classification_report
    logger.info("\n\n{}".format(report))

    cm = text_clf.confusion_matrix
    logger.info("confusion matrix:")
    logger.info("\n\n{}".format(cm))
