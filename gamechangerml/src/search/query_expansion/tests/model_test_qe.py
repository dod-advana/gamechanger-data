import logging
from gamechangerml.src.search.query_expansion.utils import remove_original_kw

import pytest

logger = logging.getLogger(__name__)


def check(expanded, exp_len):
    return 1 <= len(expanded) <= exp_len


def test_qe_emb_expand(qe_obj, topn):
    q_str = "security clearance"
    exp = qe_obj.expand(q_str, topn=topn, threshold=0.2, min_tokens=3)
    logger.info(exp)
    assert check(exp, topn)


def test_qe_emb_empty(qe_obj, topn):
    q_str = ""
    exp = qe_obj.expand(q_str, topn=topn, threshold=0.2, min_tokens=3)
    assert len(exp) == 0


def test_qe_emb_oov_1(qe_obj, topn):
    q_str = "kljljfalj"
    exp = qe_obj.expand(q_str, topn=topn, threshold=0.2, min_tokens=3)
    assert len(exp) == 0


def test_qe_emb_iv_2(qe_obj, topn):
    q_str = "financial reporting"
    exp = qe_obj.expand(q_str, topn=topn, threshold=0.2, min_tokens=3)
    assert check(exp, topn)


# @pytest.mark.parametrize(
#     "args",
#     [
#         ["passport", []],
#         [
#             "Find a book, painting, or work of art created in Santa Monica or on the west coast",
#             ["sculpture", "piece"],
#         ],  # noqa
#         ["telework policy for remote work", []],
#         ["telework policy work", ["public"]],
#     ],
# )
# def test_qe_mlm(topn, qe_mlm_obj, args):
#     query, expected = args
#     actual = qe_mlm_obj.expand(query, topn=topn, threshold=0.2, min_tokens=3)
#     assert actual == expected
