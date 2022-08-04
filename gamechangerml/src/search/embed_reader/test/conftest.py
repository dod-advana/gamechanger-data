import json
import logging
import os

import pytest

logger = logging.getLogger(__name__)
here = os.path.dirname(os.path.abspath(__file__))
test_data_path = os.path.join(here, "test_data")


@pytest.fixture(scope="session")
def query_results_ten():
    tq_json = os.path.join(test_data_path, "query_results.json")
    with open(tq_json) as fp:
        query_results = json.load(fp)
    return query_results


@pytest.fixture(scope="session")
def bad_query_results():
    tq_json = os.path.join(test_data_path, "query_results.json")
    with open(tq_json) as fp:
        query_results = json.load(fp)
    return query_results


@pytest.fixture(scope="session")
def raw_answer():
    tq_json = os.path.join(test_data_path, "ans.json")
    with open(tq_json) as fp:
        ans = json.load(fp)
    return ans


@pytest.fixture(scope="session")
def model_name():
    return "distilbert-base-uncased-distilled-squad"
