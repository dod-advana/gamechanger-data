#  Basic test
from gamechangerml.src.search.embed_reader.sparse import SparseReader
from pprint import pformat
import logging

logger = logging.getLogger(__name__)


def test_json_in(query_results_ten):
    assert "query" in query_results_ten
    assert "documents" in query_results_ten
    assert len(query_results_ten["documents"]) == 10


def test_query_in(query_results_ten, model_name):
    query = query_results_ten["query"]
    logger.info("query : {}".format(query))
    sparse_reader = SparseReader(model_name=model_name)
    assert sparse_reader

    resp = sparse_reader.predict(query_results_ten)
    logger.info(pformat(resp))
    assert resp["query"] == query
    assert len(resp["answers"]) == 10


def test_bad_query(bad_query_results, model_name):
    query = bad_query_results["query"]
    logger.info("query : {}".format(query))
    sparse_reader = SparseReader(model_name=model_name)
    assert sparse_reader

    resp = sparse_reader.predict(bad_query_results)
    logger.info(pformat(resp))
    assert resp["query"] == query
    assert len(resp["answers"]) == 10
