class QAConfig:
    """Configurations for the QA model."""

    """Base model name."""
    BASE_MODEL = "bert-base-cased-squad2"

    """Arguments used to load the model.
    
        qa_type: options are ["scored_answer", "simple_answer"]
        nbest: number of answers to retrieve from each context for comparison.
            If diff between the answer score and null answer score is greater 
            than this threshold, don't return answer.
        null_threshold
    """
    MODEL_ARGS = {
        "qa_type": "scored_answer",
        "nbest": 1,
        "null_threshold": -3,
    }
