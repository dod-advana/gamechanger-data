# flake8: noqa
# pylint: skip-file

import logging
import os
from pathlib import Path

import pandas as pd
import pytest

from gamechangerml.src.text_classif.bert_classifier import BertClassifier
from gamechangerml.src.text_classif.roberta_classifier import RobertaClassifier
from gamechangerml.src.text_classif.utils.log_init import initialize_logger

initialize_logger(to_file=True, log_name="cola-test")
logger = logging.getLogger(__name__)

try:
    here = os.path.dirname(os.path.realpath(__file__))
    p = Path(here)
    test_data_path = os.path.join(p, "test_data")
    test_data_dir = os.path.join(test_data_path, "cola_public", "raw")
    assert os.path.isdir(test_data_dir)
except (AttributeError, FileExistsError) as e:
    logger.exception("{}: {}".format(type(e), str(e)), exc_info=True)


@pytest.fixture(scope="session")
def cola_train_data():
    df = pd.read_csv(
        os.path.join(test_data_dir, "in_domain_train.tsv"),
        delimiter="\t",
        header=None,
        names=["src", "label", "l_notes", "sentence"],
    )
    sents = df.sentence.values
    labels = df.label.values
    return sents, labels


@pytest.fixture(scope="session")
def cola_train_small(cola_train_data):
    sents, labels = cola_train_data
    return sents[:1000], labels[:1000]


@pytest.fixture(scope="session")
def small_epochs():
    return 2


@pytest.fixture(scope="session")
def cola_val_data():
    df = pd.read_csv(
        os.path.join(test_data_dir, "in_domain_dev.tsv"),
        delimiter="\t",
        header=None,
        names=["src", "label", "l_notes", "sentence"],
    )
    df.sample(frac=1).reset_index(drop=True)
    sents = df.sentence.values
    labels = df.label.values
    return sents, labels


@pytest.fixture(scope="session")
def good_roberta_config():
    return os.path.join(test_data_path, "test_roberta_cola.yml")


@pytest.fixture(scope="session")
def roberta_config_4e():
    return os.path.join(test_data_path, "test_roberta_cola_4.yml")


@pytest.fixture(scope="session")
def bert_config_2e():
    return os.path.join(test_data_path, "test_bert_cola.yml")


@pytest.fixture(scope="session")
def bad_config():
    return os.path.join(test_data_path, "test_roberta_bad.yml")


@pytest.fixture(scope="session")
def bert_obj(bert_config_2e):
    return BertClassifier(bert_config_2e)


@pytest.fixture(scope="session")
def roberta_obj(good_roberta_config):
    return RobertaClassifier(good_roberta_config)


@pytest.fixture(scope="session")
def roberta_obj_4e(roberta_config_4e):
    return RobertaClassifier(roberta_config_4e)
