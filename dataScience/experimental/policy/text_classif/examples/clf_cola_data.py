import logging

import numpy as np

from dataScience.experimental.policy.text_classif.utils.data_loader import (
    load_cola,
)
from dataScience.experimental.policy.text_classif.utils.extract_features_bow import (  # noqa
    extract_features_bow,
)
from dataScience.experimental.policy.text_classif.utils.statistical import (
    run_shotgun_clf,
)
from dataScience.experimental.policy.text_classif.utils.viz import (
    plot_sg_results,
)

logger = logging.getLogger(__name__)


def exc_cola(cfg=None, data_name="COLA"):
    """
    Run the COLA data through every conceivable *bag-of-words* classifier.
    Why not? The returned results is a list of tuples. Each tuple contains
    *classifier_name, accuracy_score, train_time, test_time*.

    Args:
        cfg (Config): configuration class

        data_name (str): keep track of results with a name

    Returns:
        list

    """
    if cfg is None:
        raise ValueError("config cannot be None")

    logger.info("data set name : {}".format(data_name))
    target_names = ["OG", "IG"]

    x_train, y_train, x_dev, y_dev = load_cola()

    X_test, X_train, feat_names = extract_features_bow(
        x_train,
        x_dev,
        sublinear=cfg.sublinear,
        max_df=float(cfg.max_df),
        min_df=int(cfg.min_df),
    )

    # unused for now
    if feat_names:
        feat_names = np.asarray(feat_names)
    else:
        feat_names = None

    results = run_shotgun_clf(X_train, y_train, y_dev, X_test,)
    plot_sg_results(results, data_name=cfg.data_name, show=True)
    return results
