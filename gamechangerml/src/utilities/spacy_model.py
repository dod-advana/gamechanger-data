"""
Alex Martelli's Borg non-pattern - not a singleton

See: http://www.aleax.it/5ep.html

"""
import logging

# import en_core_web_lg
import en_core_web_md
from gamechangerml.src.utilities.borg import Borg

logger = logging.getLogger(__name__)
sp_logger = logging.getLogger("spacy")
sp_logger.setLevel(logging.ERROR)


class SpacyConfig(Borg):
    def __init__(self):
        Borg.__init__(self)

    def _set_config(self, val):
        self._value = val

    def _get_config(self):
        return getattr(self, "_value", None)

    config = property(_get_config, _set_config)


def _log_metadata(nlp):
    logger.info(
        "{} version {} vector width = {}".format(
            nlp.meta["vectors"]["name"],
            nlp.meta["version"],
            nlp.meta["vectors"]["width"],
        )
    )


def _load_spacy_name(model_name, disable):
    if model_name == "spacy-large":
        nlp = en_core_web_md.load(disable=disable)
        _log_metadata(nlp)
        logger.info("disabled components {}".format(str(disable)))
    else:
        raise ValueError("model not supported: {}".format(model_name))
    return nlp


def _set_nlp(model_name, disable=None):
    """
    Load the spaCy model

    """
    if disable is None:
        disable = list()
    c = SpacyConfig()
    if c.config is None:
        nlp = _load_spacy_name(model_name, disable)
        c.config = {"nlp": nlp}
        return c
    else:
        logger.info("using existing language model")
        return c


def get_lg_nlp():
    """
    Loads the `en_core_web_lg` model with the full pipeline.

    Returns:
        spacy.lang.en.English

    """
    try:
        c = _set_nlp(
            "spacy-large", disable=["ner", "parser", "tagger", "lemmatizer"])
        return c.config["nlp"]
    except ValueError as e:
        logger.exception("{}: {}".format(type(e), str(e)), exc_info=True)
        raise e


def get_lg_vectors():
    """
    Load the `en_core_web_lg` model with the `ner`, `parser`, and `tagger`
    pipeline components disabled. Embedding vectors remain; smaller
    faster.

    Returns:
        spacy.lang.en.English

    """
    try:
        c = _set_nlp(
            "spacy-large", disable=["ner", "parser", "tagger", "lemmatizer"])
        return c.config["nlp"]
    except ValueError as e:
        logger.exception("{}: {}".format(type(e), str(e)), exc_info=True)
        raise e


def spacy_vector_width(nlp):
    return nlp.meta["vectors"]["width"]
