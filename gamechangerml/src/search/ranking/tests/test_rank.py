import json
import logging
import os

import pytest

logger = logging.getLogger(__name__)


@pytest.fixture
def rank_obj():
    from gamechangerml.src.featurization.rank_features.rank import Rank

    return Rank()


# TODO If ICMP is enabled, try using `os.system("ping -c 1 " + host)`
@pytest.fixture
def search_data():
    import requests

    data = {"searchText": "environmental policy", "index": "game_changer", "limit": 100}
    r = None
    endpt = f"http://{os.environ.get('ML_API_HOST', 'localhost')}:9346/v2/data/documentSearch"
    try:
        r = requests.post(endpt, json=data, timeout=2)
    except requests.HTTPError:
        logger.exception("host not reachable")
    return r


@pytest.fixture
def search_data_sem():
    here = os.path.dirname(os.path.realpath(__file__))
    test_data = os.path.join(here, "sem_test.json")

    with open(test_data) as f:
        resp = json.load(f)
    return resp


def test_rank_func_sem(search_data_sem, rank_obj):

    resp = search_data_sem["docs"]
    assert rank_obj.rerank(resp)


def test_rank_func_kw(search_data, rank_obj):
    r = search_data
    if r is None:
        assert False
    resp = r.json()["docs"]
    assert rank_obj.rerank(resp)


def test_rank_func_empty(rank_obj):
    with pytest.raises(ValueError):
        rank_obj.rerank({})


def test_rank_func_alpha(rank_obj):
    with pytest.raises(ValueError):
        rank_obj.rerank({}, alpha=0.6)
