from datetime import datetime
from os import environ
import os
from gamechangerml import REPO_PATH, DATA_PATH, MODEL_PATH


class DefaultConfig:

    DATA_DIR = DATA_PATH
    LOCAL_MODEL_DIR = MODEL_PATH
    DEFAULT_FILE_PREFIX = datetime.now().strftime("%Y%m%d")


class S3Config:
    STORE_S3 = True
    S3_MODELS_DIR = "models/v3/"
    S3_CORPUS_DIR = "corpus/"


class D2VConfig:
    MODEL_ARGS = {
        "dm": 1,
        "dbow_words": 1,
        "vector_size": 50,
        "window": 5,
        "min_count": 5,
        "sample": 1e-5,
        "epochs": 20,
        "alpha": 0.020,
        "min_alpha": 0.005,
        # "workers": multiprocessing.cpu_count() // 2 # to allow some portion of the cores to perform generator tasks
    }


# for Bert Extractive Summarizer (https://pypi.org/project/bert-extractive-summarizer/)
class BertSummConfig:
    MODEL_ARGS = {
        "initialize": {
            # This gets used by the hugging face bert library to load the model, you can supply a custom trained model here
            "model": "bert-base-uncased",
            # If you have a pre-trained model, you can add the model class here.
            "custom_model": None,
            # If you have a custom tokenizer, you can add the tokenizer here.
            "custom_tokenizer": None,
            # Needs to be negative, but allows you to pick which layer you want the embeddings to come from.
            "hidden": -2,
            # It can be "mean", "median", or "max". This reduces the embedding layer for pooling.
            "reduce_option": "mean",
        },
        "fit": {
            "ratio": None,  # The ratio of sentences that you want for the final summary
            # Parameter to specify to remove sentences that are less than 40 characters
            "min_length": 40,
            "max_length": 600,  # Parameter to specify to remove sentences greater than the max length
            # Number of sentences to use. Overrides ratio if supplied.
            "num_sentences": 2,
        },
        "coreference": {"greedyness": 0.4},
        "doc_limit": 100000,
    }


class QAConfig:
    BASE_MODEL = "bert-base-cased-squad2"
    # BASE_MODEL = "multi-qa-MiniLM-L6-cos-v1"
    MODEL_ARGS = {
        # options are: ["scored_answer", "simple_answer"]
        "qa_type": "scored_answer",
        "nbest": 1,  # number of answers to retrieve from each context for comparison
        # if diff between the answer score and null answer score is greater than this threshold, don"t return answer
        "null_threshold": -3,
    }


class EmbedderConfig:
    BASE_MODEL = "msmarco-distilbert-base-v2"
    MODEL_ARGS = {
        "min_token_len": 25,
        "verbose": True,  # for creating LocalCorpus
        "return_id": True,  # for creating LocalCorpus
    }
    FINETUNE = {"shuffle": True, "batch_size": 32, "epochs": 3, "warmup_steps": 100}
    DEFAULT_THRESHOLD = 0.7  # if no threshold is recommended in evals, this is the default min score for the sent index
    THRESHOLD_MULTIPLIER = (
        0.8  # makes the default threshold less strict (to use exact default, set to 1)
    )


class SimilarityConfig:
    BASE_MODEL = "distilbart-mnli-12-3"


class DocCompareEmbedderConfig:
    BASE_MODEL = "msmarco-distilbert-base-v2"
    MODEL_ARGS = {
        "min_token_len": 25,
        "verbose": True,  # for creating LocalCorpus
        "return_id": True,  # for creating LocalCorpus
    }
    FINETUNE = {"shuffle": True, "batch_size": 32,
                "epochs": 3, "warmup_steps": 100}


class DocCompareSimilarityConfig:
    BASE_MODEL = "distilbart-mnli-12-3"


class QexpConfig:
    MODEL_ARGS = {
        "init": {  # args for creating QE object
            "qe_files_dir": os.path.join(
                REPO_PATH, "gamechangerml", "src", "search", "query_expansion"
            ),
            "method": "emb",
        },
        "expansion": {  # configs for getting expanded terms
            "topn": 2,
            "threshold": 0.2,
            "min_tokens": 3,
        },
        "bqe": {
            "num_trees": 125,
            "num_keywords": 2,
            "ngram": (1, 3),
            "abbrv_file": None,
            "merge_word_sim": True,
        },
    }


class ValidationConfig:
    DATA_ARGS = {
        # need to have validation data in here
        "validation_dir": os.path.join(DATA_PATH, "validation"),
        "evaluation_dir": os.path.join(DATA_PATH, "evaluation"),
        "user_dir": os.path.join(DATA_PATH, "user_data"),
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
        "question_gc": {"queries": "domain/question_answer/QA_domain_data.json"},
        "retriever_gc": {"gold_standard": "gold_standard.csv"},
        "matamo_dir": os.path.join(DATA_PATH, "user_data", "matamo_feedback"),
        "search_hist_dir": os.path.join(DATA_PATH, "user_data", "search_history"),
        "qe_gc": "domain/query_expansion/QE_domain.json",
    }

    TRAINING_ARGS = {
        "start_date": "2020-12-01",  # earliest date to include search hist/feedback data from
        "end_date": "2025-12-01",  # last date to include search hist/feedback data from
        "exclude_searches": ["pizza", "shark"],
        "min_correct_matches": {"gold": 3, "silver": 2, "any": 0},
        "max_results": {"gold": 7, "silver": 10, "any": 100},
    }


class TrainingConfig:
    DATA_ARGS = {
        "training_data_dir": os.path.join(DATA_PATH, "training"),
        "train_test_split_ratio": 0.8,
    }


class TopicsConfig:

    # topic models should be in folders named gamechangerml/models/topic_model_<date>
    # this path will look for bigrams.phr, tfidf.model, tfidf_dictionary.dic in gamechangerml/models folder as a last resort
    DATA_ARGS = {"LOCAL_MODEL_DIR": MODEL_PATH}
