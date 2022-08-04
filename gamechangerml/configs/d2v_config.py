class D2VConfig:
    """Configurations for Doc2Vec model."""
    
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
    }
