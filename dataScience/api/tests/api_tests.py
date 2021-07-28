import requests
import logging
import pytest
import os
import json
import sys

from dataScience.src.search.query_expansion.utils import remove_original_kw
from .test_examples import TestSet

logger = logging.getLogger()
GC_ML_HOST = os.environ.get("GC_ML_HOST", default="localhost")
API_URL = f"http://{GC_ML_HOST}:5000"


def test_conn():
    resp = requests.get(API_URL)
    assert resp.ok == True


def test_expandTerms():
    test_data = {"termsList": ["artificial intelligence"]}
    resp = requests.post(API_URL + "/expandTerms", json=test_data)
    verified = {"artificial intelligence": [
        '"intelligence"', '"human intelligence"']}
    assert resp.json() == verified


# this is in here because it is based off of api function flow not specifically qe
def test_remove_kw_1():
    test_term = "network"
    test_list = ["network connection", "communications network"]
    terms = remove_original_kw(test_list, test_term)
    verified = ["connection", "communications"]
    assert terms == verified


def test_remove_kw_2():
    test_term = "animal"
    test_list = ["animals", "animal cruelty"]
    terms = remove_original_kw(test_list, test_term)
    verified = ["animals", "cruelty"]
    assert terms == verified


def test_remove_kw_3():
    test_term = "american navy"
    test_list = ["british navy", "navy washington"]
    terms = remove_original_kw(test_list, test_term)
    verified = ["british navy", "navy washington"]
    assert terms == verified


def test_remove_kw_4():
    test_term = "weapons"
    test_list = ["enemy weapons", "weapons explosives"]
    terms = remove_original_kw(test_list, test_term)
    verified = ["enemy", "explosives"]
    assert terms == verified


def test_getTransformerList():
    resp = requests.get(API_URL + "/getTransformerList")
    verified = TestSet.transformer_list_expect
    assert resp.json() == verified
    return verified


def test_postSentSearch():
    test_data = TestSet.sentence_test_data
    verified = TestSet.sentence_search_expect

    resp = requests.post(API_URL + "/transSentenceSearch", json=test_data)

    assert resp.json() == verified
    return verified


def getCurrentTrans():
    resp = requests.get(API_URL + "/getCurrentTransformer")
    return resp.json()


def test_transformerSearch():
    test_data = TestSet.transformer_test_data
    verified = TestSet.transformer_search_expect

    resp = requests.post(API_URL + "/transformerSearch", json=test_data)
    assert resp.json() == verified

def test_transformerSearch():
    test_data = TestSet.qa_test_data
    verified = TestSet.qa_expect

    resp = requests.post(API_URL + "/questionAnswer", json=test_data)
    assert resp.json() == verified



def test_changeModels():
    import time

    test_transformer = "distilroberta-base"
    model_dict = {"model_name": test_transformer}
    resp = requests.post(API_URL + "/updateModel", json=model_dict)
    time.sleep(10)
    curr = getCurrentTrans()
    assert curr["model_name"] == resp.json()["model_name"]
