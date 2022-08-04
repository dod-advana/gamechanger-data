from os.path import join
from gamechangerml import DATA_PATH


class ValidationConfig:
    DATA_ARGS = {
        # need to have validation data in here
        "validation_dir": join(DATA_PATH, "validation"),
        "evaluation_dir": join(DATA_PATH, "evaluation"),
        "user_dir": join(DATA_PATH, "user_data"),
        "test_corpus_dir": "gamechangerml/test_corpus",
        "squad": {
            "dev": "original/squad2.0/dev-v2.0.json",
            "train": "original/squad2.0/train-v2.0.json",
        },
        "nli": {
            "matched": "original/multinli_1.0/multinli_1.0_dev_matched.jsonl",
            "mismatched": "original/multinli_1.0/multinli_1.0_dev_mismatched.jsonl",
        },
        "msmarco": {
            "collection": "original/msmarco_1k/collection.json",
            "queries": "original/msmarco_1k/queries.json",
            "relations": "original/msmarco_1k/relations.json",
            "metadata": "original/msmarco_1k/metadata.json",
        },
        "question_gc": {
            "queries": "domain/question_answer/QA_domain_data.json"
        },
        "retriever_gc": {"gold_standard": "gold_standard.csv"},
        "matamo_dir": join(DATA_PATH, "user_data", "matamo_feedback"),
        "search_hist_dir": join(DATA_PATH, "user_data", "search_history"),
        "qe_gc": "domain/query_expansion/QE_domain.json",
    }

    TRAINING_ARGS = {
        "start_date": "2020-12-01",  # earliest date to include search hist/feedback data from
        "end_date": "2025-12-01",  # last date to include search hist/feedback data from
        "exclude_searches": ["pizza", "shark"],
        "min_correct_matches": {"gold": 3, "silver": 2, "any": 0},
        "max_results": {"gold": 7, "silver": 10, "any": 100},
    }

