import logging
import pytest

logger = logging.getLogger(__name__)


@pytest.mark.parametrize(
    "args",
    [
        ["passport", []],
        [
            "Find a book, painting, or work of art created in Santa Monica or on the west coast",  # noqa
            ["sculpture", "piece"],
        ],
        ["telework policy for remote work", []],
        ["telework policy work", ["public"]],
    ],
)
def test_qe_mlm(qe_mlm, args):
    q_str, expected = args
    actual = qe_mlm.predict(q_str, threshold=0.2, top_n=2)
    assert actual == expected
