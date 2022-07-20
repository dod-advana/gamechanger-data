import logging
import os
from pathlib import Path
import pytest

from gamechangerml.src.search.sent_transformer.model import *
from gamechangerml import REPO_PATH

logger = logging.getLogger(__name__)


def test_sent_search(sent_dirs, topn):
    """
    Test for performing a search
    """
    test_data_dir, test_data_2_dir, test_index_dir = sent_dirs

    here = os.path.dirname(os.path.realpath(__file__))
    p = Path(here)
    gc_path = REPO_PATH

    sim_model_path = os.path.join(
        str(gc_path), "gamechangerml/models/transformers/distilbart-mnli-12-3"
    )

    sent_searcher = SentenceSearcher(test_index_dir, sim_model=sim_model_path)

    queries = ["regulation", "Major Automated Information System"]
    for query in queries:
        results = sent_searcher.search(query, n_returns=topn)
        assert len(results) == topn
