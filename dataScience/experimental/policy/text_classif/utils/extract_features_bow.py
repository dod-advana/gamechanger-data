import logging
from time import time

from sklearn.feature_extraction.text import TfidfVectorizer

logger = logging.getLogger(__name__)


def extract_features_bow(
    X_train, X_test, max_df=1.0, min_df=1, sublinear=False, stop_words=None
):
    """
    Create the *tf-idf* matrix for training and testing.

    Args:
        X_train (np.array) : training data

        X_test (np.array) : test data

        max_df (float|int): See scikit-learn vectorizer documentation

        min_df (float|int): See scikit-learn vectorizer documentation

        sublinear (bool): See scikit-learn vectorizer documentation

        stop_words(list|None): if `None`, use the default "english"; else
            use the list

    Returns:
        np.array, np.array, list

    """
    if stop_words is None:
        stop_words = "english"

    start = time()
    vectorizer = TfidfVectorizer(
        sublinear_tf=sublinear,
        max_df=max_df,
        min_df=min_df,
        stop_words=stop_words,
    )

    X_train_ = vectorizer.fit_transform(X_train)
    r, c = X_train_.shape
    logger.info("x_train_ : {} x {}".format(r, c))

    X_test_ = vectorizer.transform(X_test)
    r, c = X_test_.shape
    logger.info("x_test_ : {} x {}".format(r, c))

    feature_names = vectorizer.get_feature_names()
    logger.info("done in {:4.4f}s".format(time() - start))

    return X_test_, X_train_, feature_names
