import requests
import logging
import pytest
import os
import json
import sys
import time

from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from http.client import HTTPConnection  # py3

from gamechangerml.src.search.query_expansion.utils import remove_original_kw
from gamechangerml.src.text_handling.process import preprocess
from gamechangerml.src.utilities.text_utils import (
    has_many_short_tokens,
    has_many_repeating,
    has_extralong_tokens,
    is_a_toc,
    check_quality_paragraph,
)

# from gamechangerml import DATA_PATH

from .test_examples import TestSet

logger = logging.getLogger()
GC_ML_HOST = os.environ.get("GC_ML_HOST", default="localhost")
API_URL = f"{GC_ML_HOST}:5000" if "http" in GC_ML_HOST else f"http://{GC_ML_HOST}:5000"
QA_TIMEOUT = 30


retries = Retry(total=10, backoff_factor=1)
adapter = HTTPAdapter(max_retries=retries)
http = requests.Session()


def test_conn():
    resp = http.get(API_URL)
    assert resp.ok == True


def test_expand_terms():
    test_data = {"termsList": ["artificial intelligence"]}
    resp = http.post(API_URL + "/expandTerms", json=test_data)
    verified = {
        "qexp": {
            "artificial intelligence": [
                '"employ artificial intelligence"',
                '"developing artificial intelligence"',
            ]
        },
        "wordsim": {"artificial": ["artifical"], "intelligence": ["intellegence"]},
    }
    assert resp.json() == verified


def test_expand_terms_proper_fields_qexp():
    test_data = {"termsList": ["artificial intelligence"]}
    resp = http.post(API_URL + "/expandTerms", json=test_data)
    print(resp)
    data = resp.json()
    if "qexp" in data.keys():
        assert True
    else:
        assert False


def test_expand_terms_proper_fields_wordsim():
    test_data = {"termsList": ["artificial intelligence"]}
    resp = http.post(API_URL + "/expandTerms", json=test_data)
    data = resp.json()
    if "wordsim" in data.keys():
        assert True
    else:
        assert False


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


def test_get_transformer_list():
    resp = http.get(API_URL + "/getModelsList")
    verified = TestSet.transformer_list_expect
    response = resp.json()
    trans = len(list(response["transformers"].keys()))
    assert trans > 0
    return verified


def get_current_trans():
    resp = http.get(API_URL + "/getCurrentTransformer")
    return resp.json()


# Sent Index Processing Tests


def test_has_many_short_tokens():
    test_pars = TestSet.sent_index_processing_pars
    results = []
    for x in test_pars.keys():
        text = test_pars[x]
        tokens = preprocess(text)
        check = has_many_short_tokens(tokens, threshold=4.0)
        results.append(check)
    assert results == TestSet.sent_index_processing_results["has_many_short_tokens"]


def test_has_many_repeating():
    test_pars = TestSet.sent_index_processing_pars
    results = []
    for x in test_pars.keys():
        text = test_pars[x]
        tokens = preprocess(text)
        check = has_many_repeating(text, tokens, threshold=0.6)
        results.append(check)
    assert results == TestSet.sent_index_processing_results["has_many_repeating"]


def test_has_extralong_tokens():
    test_pars = TestSet.sent_index_processing_pars
    results = []
    for x in test_pars.keys():
        text = test_pars[x]
        check = has_extralong_tokens(text, threshold=25)
        results.append(check)
    assert results == TestSet.sent_index_processing_results["has_extralong_tokens"]


def test_is_a_toc():
    test_pars = TestSet.sent_index_processing_pars
    results = []
    for x in test_pars.keys():
        text = test_pars[x]
        check = is_a_toc(text)
        results.append(check)
    assert results == TestSet.sent_index_processing_results["is_a_toc"]


def test_check_quality_paragraph():
    test_pars = TestSet.sent_index_processing_pars
    results = []
    for x in test_pars.keys():
        text = test_pars[x]
        tokens = preprocess(text)
        check = check_quality_paragraph(tokens, text)
        results.append(check)
    assert results == TestSet.sent_index_processing_results["check_quality"]


# def test_changeModels():

#     test_index = "sent_index_20210715"
#     model_dict = {"sentence": test_index}
#     resp = http.post(API_URL + "/reloadModels", json=model_dict)
#     time.sleep(20)
#     curr = getCurrentTrans()
#     assert curr["sentence_index"] == "gamechangerml/models/sent_index_20210715"

# Search Tests


def test_post_sent_search():
    test_data = TestSet.sentence_test_data
    verified = TestSet.sentence_search_expect

    resp = http.post(API_URL + "/transSentenceSearch", json=test_data)

    # assert [{'id':resp['id'],'text':resp['text']} for resp in resp.json()] == [{'id':resp['id'],'text':resp['text']} for resp in verified]
    # for i in range(0,len(verified)):
    #     assert abs(resp.json()[i]['score'] - verified[i]['score']) < .01
    assert len(resp.json()) > 5


def test_sent_search_dupes():
    test_data = TestSet.sentence_test_data
    verified = TestSet.sentence_search_expect

    resp = http.post(API_URL + "/transSentenceSearch", json=test_data)
    resp_data = resp.json()
    num_results = len(resp_data)
    print(num_results)
    unique = set([x["id"] for x in resp_data])
    if len(unique) == num_results:
        assert True
    else:
        assert False


def test_sent_search_proper_fields_id():
    test_data = TestSet.sentence_test_data
    verified = TestSet.sentence_search_expect

    resp = http.post(API_URL + "/transSentenceSearch", json=test_data)
    resp_data = resp.json()
    if "id" in resp_data[0].keys():
        assert True


def test_sent_search_proper_fields_text():
    test_data = TestSet.sentence_test_data
    verified = TestSet.sentence_search_expect

    resp = http.post(API_URL + "/transSentenceSearch", json=test_data)
    resp_data = resp.json()
    if "text" in resp_data[0].keys():
        assert True


def test_sentSearch_properFields_threshold():
    test_data = TestSet.sentence_test_data
    verified = TestSet.sentence_search_expect

    resp = http.post(API_URL + "/transSentenceSearch", json=test_data)
    resp_data = resp.json()
    if "threshold" in resp_data[0].keys():
        assert True


def test_sent_search_has_text():
    test_data = TestSet.sentence_test_data
    verified = TestSet.sentence_search_expect

    resp = http.post(API_URL + "/transSentenceSearch", json=test_data)
    resp_data = resp.json()
    allHaveText = True
    for doc in resp_data:
        if len(doc["text"]) < 1:
            allHaveText = False
    assert allHaveText


def test_sent_search_threshold():
    test_data = TestSet.sentence_test_data
    # threshold = "0.6"
    resp = http.post(
        API_URL + "/transSentenceSearch?threshold=0.5", json=test_data)
    resp_data = resp.json()
    for i in resp_data:
        if float(i["score"]) >= 0.5:
            assert int(i["passing_result"]) == 1
        else:
            assert int(i["passing_result"]) == 0


def test_recommender():
    test_data = TestSet.recommender_data
    expected = TestSet.recommender_results

    resp = http.post(API_URL + "/recommender", json=test_data)
    data = resp.json()
    print(data)
    assert len(data["results"]) == 5
    assert len(set(expected["results"]).intersection(data["results"])) > 0


# QA Tests


def send_qa(query, context):

    start = time.perf_counter()
    post = {"query": query, "search_context": context}
    data = json.dumps(post).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    response = http.post(API_URL + "/questionAnswer",
                         data=data, headers=headers)

    end = time.perf_counter()
    took = float(f"{end-start:0.4f}")

    return response.json(), took


def test_qa_regular():
    query = "when is marijuana legalized"
    expected = "it will be legal to grow up to four marijuana plants beginning July 1"
    resp, took = send_qa(query, TestSet.qa_test_context_1)
    top_answer = resp["answers"][0]["text"]
    scores = [i["null_score_diff"] for i in resp["answers"]]
    print(
        "\nQUESTION: ", query, "\nANSWER: ", top_answer, f"\n (took {took} seconds)\n"
    )
    assert top_answer == expected  # assert response is right
    # assert took < QA_TIMEOUT # assert time
    assert resp["answers"][0]["null_score_diff"] == min(
        scores
    )  # assert is best scoring answer


def test_qa_one_question():
    query = "when is marijuana legalized?"
    expected = "it will be legal to grow up to four marijuana plants beginning July 1"
    resp, took = send_qa(query, TestSet.qa_test_context_1)
    top_answer = resp["answers"][0]["text"]
    scores = [i["null_score_diff"] for i in resp["answers"]]
    print(
        "\nQUESTION: ", query, "\nANSWER: ", top_answer, f"\n (took {took} seconds)\n"
    )
    assert top_answer == expected  # assert response is right
    # assert took < QA_TIMEOUT # assert time
    assert resp["answers"][0]["null_score_diff"] == min(
        scores
    )  # assert is best scoring answer


def test_qa_multiple_question():
    query = "when is marijuana legalized???"
    expected = "it will be legal to grow up to four marijuana plants beginning July 1"
    resp, took = send_qa(query, TestSet.qa_test_context_1)
    top_answer = resp["answers"][0]["text"]
    scores = [i["null_score_diff"] for i in resp["answers"]]
    print(
        "\nQUESTION: ", query, "\nANSWER: ", top_answer, f"\n (took {took} seconds)\n"
    )
    assert top_answer == expected  # assert response is right
    # assert took < QA_TIMEOUT # assert time
    assert resp["answers"][0]["null_score_diff"] == min(
        scores
    )  # assert is best scoring answer


def test_qa_allcaps():
    query = "WHEN IS MARIJUANA LEGALIZED"
    expected = "it will be legal to grow up to four marijuana plants beginning July 1"
    resp, took = send_qa(query, TestSet.qa_test_context_1)
    top_answer = resp["answers"][0]["text"]
    scores = [i["null_score_diff"] for i in resp["answers"]]
    print(
        "\nQUESTION: ", query, "\nANSWER: ", top_answer, f"\n (took {took} seconds)\n"
    )
    assert top_answer == expected  # assert response is right
    # assert took < QA_TIMEOUT # assert time
    assert resp["answers"][0]["null_score_diff"] == min(
        scores
    )  # assert is best scoring answer


def test_qa_apostrophe():
    query = "when's marijuana legalized"
    expected = "it will be legal to grow up to four marijuana plants beginning July 1"
    resp, took = send_qa(query, TestSet.qa_test_context_1)
    top_answer = resp["answers"][0]["text"]
    scores = [i["null_score_diff"] for i in resp["answers"]]
    print(
        "\nQUESTION: ", query, "\nANSWER: ", top_answer, f"\n (took {took} seconds)\n"
    )
    assert top_answer == expected  # assert response is right
    # assert took < QA_TIMEOUT # assert time
    assert resp["answers"][0]["null_score_diff"] == min(
        scores
    )  # assert is best scoring answer


def test_qa_past_tense():
    query = "when was marijuana legalized?"
    expected = "Wednesday"
    resp, took = send_qa(query, TestSet.qa_test_context_1)
    top_answer = resp["answers"][0]["text"]
    scores = [i["null_score_diff"] for i in resp["answers"]]
    print(
        "\nQUESTION: ", query, "\nANSWER: ", top_answer, f"\n (took {took} seconds)\n"
    )
    assert top_answer == expected  # assert response is right
    # assert took < QA_TIMEOUT # assert time
    assert resp["answers"][0]["null_score_diff"] == min(
        scores
    )  # assert is best scoring answer


def test_qa_future_tense():
    query = "when will marijuana be legal?"
    expected = "it will be legal to grow up to four marijuana plants beginning July 1"
    resp, took = send_qa(query, TestSet.qa_test_context_1)
    top_answer = resp["answers"][0]["text"]
    scores = [i["null_score_diff"] for i in resp["answers"]]
    print(
        "\nQUESTION: ", query, "\nANSWER: ", top_answer, f"\n (took {took} seconds)\n"
    )
    assert top_answer == expected  # assert response is right
    # assert took < QA_TIMEOUT # assert time
    assert resp["answers"][0]["null_score_diff"] == min(
        scores
    )  # assert is best scoring answer


def test_qa_specific():
    query = "when will marijuana be legal in Virginia?"
    expected = "it will be legal to grow up to four marijuana plants beginning July 1"
    resp, took = send_qa(query, TestSet.qa_test_context_1)
    top_answer = resp["answers"][0]["text"]
    scores = [i["null_score_diff"] for i in resp["answers"]]
    print(
        "\nQUESTION: ", query, "\nANSWER: ", top_answer, f"\n (took {took} seconds)\n"
    )
    assert top_answer == expected  # assert response is right
    # assert took < QA_TIMEOUT # assert time
    assert resp["answers"][0]["null_score_diff"] == min(
        scores
    )  # assert is best scoring answer


def test_qa_outside_scope():
    query = "what is the capital of Assyria?"
    expected = ""
    resp, took = send_qa(query, TestSet.qa_test_context_1)
    top_answer = resp["answers"][0]["text"]
    scores = [i["null_score_diff"] for i in resp["answers"]]
    print(
        "\nQUESTION: ", query, "\nANSWER: ", top_answer, f"\n (took {took} seconds)\n"
    )
    assert top_answer == expected  # assert response is right
    # assert took < QA_TIMEOUT # assert time
    assert resp["answers"][0]["null_score_diff"] == min(
        scores
    )  # assert is best scoring answer


def test_get_current_models():
    expected = ""
    resp = http.get(API_URL + "/getLoadedModels")
    resp_data = resp.json()
    assert type(resp_data) == dict


def test_get_current_models_not_empty():
    expected = ""
    resp = http.get(API_URL + "/getLoadedModels")
    resp_data = resp.json()
    assert len(resp_data.keys()) > 0


def test_data_dir():
    resp = http.get(API_URL + "/getDataList")
    resp_data = resp.json()
    assert type(resp_data) == dict


def test_data_dir_not_empty():
    resp = http.get(API_URL + "/getDataList")
    resp_data = resp.json()
    if resp_data["dirs"]:
        assert True


# Train Model tests

# def test_trainModel_sentence():
#     model_dict = {
#         "build_type": "sentence",
#         "corpus": os.path.join(DATA_PATH, "test_data"), # should have 3 test docs
#         "encoder_model": "msmarco-distilbert-base-v2",
#         "gpu": False,
#         "upload": False,
#         "version": "TEST"
#     }
#     resp = http.post(API_URL + "/trainModel", json=model_dict)
#     assert resp.ok == True

# def test_trainModel_eval_squad():
#     model_dict = {
#         "build_type": "eval",
#         "model_name": "bert-base-cased-squad2",
#         "eval_type": "original",
#         "sample_limit": 10,
#         "validation_data": "latest"
#     }
#     resp = http.post(API_URL + "/trainModel", json=model_dict)
#     assert resp.ok == True

# def test_trainModel_eval_msmarco():
#     model_dict = {
#         "build_type": "eval",
#         "model_name": "msmarco-distilbert-base-v2",
#         "eval_type": "original",
#         "sample_limit": 10,
#         "validation_data": "latest"
#     }
#     resp = http.post(API_URL + "/trainModel", json=model_dict)
#     assert resp.ok == True

# def test_trainModel_eval_nli():
#     model_dict = {
#         "build_type": "eval",
#         "model_name": "distilbart-mnli-12-3",
#         "eval_type": "original",
#         "sample_limit": 10,
#         "validation_data": "latest"
#     }
#     resp = http.post(API_URL + "/trainModel", json=model_dict)
#     assert resp.ok == True

# def test_TrainModel_meta():
#     model_dict = {
#         "build_type": "meta",
#     }
#     resp = http.post(API_URL + "/trainModel", json=model_dict)
#     assert resp.ok == True
