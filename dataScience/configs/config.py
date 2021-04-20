from datetime import datetime
from os import environ


class DefaultConfig:

    DATA_DIR = "common/data/processed"
    LOCAL_MODEL_DIR = "dataScience/models"
    DEFAULT_FILE_PREFIX = datetime.now().strftime("%Y%m%d")
    # DEFAULT_MODEL_NAME = "20200728"
    # MODEL_DIR = "dataScience/src/modelzoo/semantic/packaged_models/20200728"
    # LOCAL_PACKAGED_MODELS_DIR = "dataScience/src/modelzoo/semantic/packaged_models"


class S3Config:
    STORE_S3 = True
    S3_MODELS_DIR = "models/v3/"
    S3_CORPUS_DIR = "corpus/"


class D2VConfig:
    # MODEL_ID = datetime.now().strftime("%Y%m%d")
    # MODEL_DIR = "dataScience/src/modelzoo/semantic/models"
    # CORPUS_DIR = "../tinytestcorpus"
    # CORPUS_DIR = "test/small_corpus"
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
        # 'workers': multiprocessing.cpu_count() // 2 # to allow some portion of the cores to perform generator tasks
    }


# for Bert Extractive Summarizer (https://pypi.org/project/bert-extractive-summarizer/)
class BertSummConfig:
    MODEL_ARGS = {
        "initialize": {
            # This gets used by the hugging face bert library to load the model, you can supply a custom trained model here
            "model": 'bert-base-uncased',
            # If you have a pre-trained model, you can add the model class here.
            "custom_model": None,
            # If you have a custom tokenizer, you can add the tokenizer here.
            "custom_tokenizer":  None,
            # Needs to be negative, but allows you to pick which layer you want the embeddings to come from.
            "hidden": -2,
            # It can be 'mean', 'median', or 'max'. This reduces the embedding layer for pooling.
            "reduce_option": 'mean'
        },
        "fit": {
            "ratio": None,  # The ratio of sentences that you want for the final summary
            # Parameter to specify to remove sentences that are less than 40 characters
            "min_length": 40,
            "max_length": 600,  # Parameter to specify to remove sentences greater than the max length
            # Number of sentences to use. Overrides ratio if supplied.
            "num_sentences": 2
        },
        "coreference": {
            "greedyness": 0.4
        },
        "doc_limit": 100000
    }
