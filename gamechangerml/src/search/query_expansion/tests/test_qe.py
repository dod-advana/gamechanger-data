import logging

import pytest

logger = logging.getLogger(__name__)


def check(expanded, exp_len):
    return 1 <= len(expanded) <= exp_len


def test_qe_emb_expand(qe_obj, topn):
    q_str = "security clearance"
    exp = qe_obj.expand(q_str)
    logger.info(exp)
    assert check(exp, topn)


def test_qe_emb_empty(qe_obj, topn):
    q_str = ""
    exp = qe_obj.expand(q_str, topn=topn)
    assert len(exp) == 0


def test_qe_emb_oov_1(qe_obj, topn):
    q_str = "kljljfalj"
    exp = qe_obj.expand(q_str, topn=topn)
    assert len(exp) == 0


def test_qe_emb_iv_2(qe_obj, topn):
    q_str = "financial reporting"
    exp = qe_obj.expand(q_str, topn=topn)
    logger.info(exp)
    assert check(exp, topn)


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


@pytest.mark.parametrize(
    "args",
    [
        ["passport", []],
        [
            "Find a book, painting, or work of art created in Santa Monica or on the west coast",
            ["sculpture", "piece"],
        ],  # noqa
        ["telework policy for remote work", []],
        ["telework policy work", ["public"]],
    ],
)
def test_qe_mlm(topn, qe_mlm_obj, args):
    query, expected = args
    actual = qe_mlm_obj.expand(query, topn=topn, threshold=0.2, min_tokens=3)
    logger.info(actual)
    assert actual == expected
