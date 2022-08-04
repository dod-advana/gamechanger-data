class DocCompareEmbedderConfig:
    """Configurations for the Document Comparison Encoder model."""

    """Base model name."""
    BASE_MODEL = "msmarco-distilbert-base-v2"

    """Arguments used to load the model.

        min_token_len
        verbose: for creating LocalCorpus
        return_id: LocalCorpus
    """
    MODEL_ARGS = {
        "min_token_len": 25,
        "verbose": True,
        "return_id": True,
    }

    FINETUNE = {
        "shuffle": True,
        "batch_size": 32,
        "epochs": 3,
        "warmup_steps": 100,
    }
