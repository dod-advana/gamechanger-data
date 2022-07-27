class EmbedderConfig:
    """Configurations for the Sentence Encoder model."""

    """Base model name"""
    BASE_MODEL = "msmarco-distilbert-base-v2"

    """Arguments used to load the model.
    
        min_token_len
        verbose: for creating LocalCorpus
        return_id: for creating LocalCorpus
    """
    MODEL_ARGS = {
        "min_token_len": 25,
        "verbose": True,
        "return_id": True,
    }

    """Arguments for STFinetuner."""
    FINETUNE = {
        "shuffle": True,
        "batch_size": 32,
        "epochs": 3,
        "warmup_steps": 100,
    }

    """If no threshold is recommended in evaluations, this is the default 
    minimum score for the sentence index.
    """
    DEFAULT_THRESHOLD = 0.7

    """Makes the default threshold less strict. To use exact default, set to 1."""
    THRESHOLD_MULTIPLIER = 0.8

    SENT_INDEX = "sent_index_20210715"
