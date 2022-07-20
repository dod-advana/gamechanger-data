# flake8: noqa
# pylint: skip-file

import logging
import os
from pathlib import Path

import pytest

from gamechangerml.src.search.sent_transformer.model import *
from gamechangerml import REPO_PATH

log_fmt = (
    "[%(asctime)s %(levelname)-8s], [%(filename)s:%(lineno)s - "
    + "%(funcName)s()], %(message)s"
)
logging.basicConfig(level=logging.DEBUG, format=log_fmt)
logger = logging.getLogger(__name__)

try:
    here = os.path.dirname(os.path.realpath(__file__))
    p = Path(here)
    gc_path = REPO_PATH
    test_data_dir = os.path.join(str(p), "test_data")
    test_data_2_dir = os.path.join(str(p), "test_data_2")
    test_index_dir = os.path.join(str(p), "test_index")

    encoder_model_path = os.path.join(
        str(gc_path), "gamechangerml/models/transformers/msmarco-distilbert-base-v2"
    )
    assert os.path.isdir(test_data_dir)
    assert os.path.isdir(test_index_dir)
except (AttributeError, FileExistsError) as e:
    logger.exception("{}: {}".format(type(e), str(e)), exc_info=True)


@pytest.fixture(scope="session")
def sent_dirs():
    return test_data_dir, test_data_2_dir, test_index_dir


@pytest.fixture(scope="session")
def sent_encoder():
    return SentenceEncoder(encoder_model_path)


@pytest.fixture(scope="session")
def sent_searcher():
    return SentenceSearcher(test_index_dir)


@pytest.fixture(scope="session")
def topn():
    return 10


@pytest.fixture(scope="session")
def index_files():
    return ["config", "data.csv", "doc_ids.txt", "embeddings", "embeddings.npy"]
