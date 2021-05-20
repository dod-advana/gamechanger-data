import logging
import os
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

here = os.path.dirname(os.path.realpath(__file__))
p = Path(here)


def load_cola():
    """
    Load sentences from the Corpus of Linguistic Acceptability (COLA)

    Returns:
        list, np.array, list, np.array

    """
    path_from_here = os.path.join(
        p.parents[0], "tests", "test_data", "cola_public", "raw"
    )
    logger.info("path : {}".format(path_from_here))
    train_path = os.path.join(path_from_here, "in_domain_train.tsv")

    # give it a shuffle
    data_df = pd.read_csv(train_path, delimiter="\t")
    data_df = data_df.sample(frac=1).reset_index(drop=True)

    train_split = int(len(data_df) * 0.90)
    logger.info("train split : {}".format(train_split))

    x_train = list(data_df.iloc[:, 3])[:train_split]
    y_train = np.array(data_df.iloc[:, 1])[:train_split]
    x_test = list(data_df.iloc[:, 3])[train_split:]
    y_test = np.array(data_df.iloc[:, 1])[train_split:]

    return x_train, y_train, x_test, y_test
