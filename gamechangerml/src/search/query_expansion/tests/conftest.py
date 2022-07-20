# flake8: noqa
# pylint: skip-file

import logging
import os
from pathlib import Path

import pytest

from gamechangerml.src.search.query_expansion.build_ann_cli.build_qe_model import (  # noqa
    main,
)
from gamechangerml.src.search.query_expansion.qe import QE

log_fmt = (
    "[%(asctime)s %(levelname)-8s], [%(filename)s:%(lineno)s - "
    + "%(funcName)s()], %(message)s"
)
logging.basicConfig(level=logging.DEBUG, format=log_fmt)
logger = logging.getLogger(__name__)

try:
    here = os.path.dirname(os.path.realpath(__file__))
    p = Path(here)
    test_data_dir = os.path.join(p.parents[3], "data", "test_data")
    aux_path = os.path.join(str(p.parent), "aux_data")
    word_wt = os.path.join(aux_path, "enwiki_vocab_min200.txt")
    assert os.path.isfile(word_wt)
except (AttributeError, FileExistsError) as e:
    logger.exception("{}: {}".format(type(e), str(e)), exc_info=True)


@pytest.fixture(scope="session")
def ann_index_dir(tmpdir_factory):
    fn = tmpdir_factory.mktemp("data")
    return str(fn)


@pytest.fixture(scope="session")
def qe_obj(ann_index_dir):
    main(test_data_dir, ann_index_dir, word_wt_file=word_wt)
    return QE(
        ann_index_dir, method="emb", vocab_file="enwiki_vocab_min200.txt"
    )


@pytest.fixture(scope="session")
def qe_mlm_obj():
    return QE(None, method="mlm")


@pytest.fixture(scope="session")
def topn():
    return 2
