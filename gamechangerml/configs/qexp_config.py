from os.path import join
from gamechangerml import REPO_PATH


class QexpConfig:
    """Configurations for the Query Expansion (QE) model."""

    """Arguments for loading the QE object."""
    INIT_ARGS = {
        "qe_files_dir": join(
            REPO_PATH, "gamechangerml", "src", "search", "query_expansion"
        ),
        "method": "emb",
    }

    """Arguments for getting expanded terms."""
    EXPANSION_ARGS = {
        "topn": 2,
        "threshold": 0.2,
        "min_tokens": 3,
    }

    """Arguments for building the QE model."""
    BUILD_ARGS = {
        "num_trees": 125,
        "num_keywords": 2,
        "ngram": (1, 3),
        "abbrv_file": None,
        "merge_word_sim": True,
    }
