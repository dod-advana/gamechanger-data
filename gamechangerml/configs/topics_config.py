from gamechangerml import MODEL_PATH


class TopicsConfig:
    """Configurations for the Topic Model."""

    """Topic models should be in the folder 
    gamechangerml/models/topic_model_<date>
    and should contain bigrams.phr, tfidf.model, and tfidf_dictionary.dic.
    """
    DATA_ARGS = {"LOCAL_MODEL_DIR": MODEL_PATH}

