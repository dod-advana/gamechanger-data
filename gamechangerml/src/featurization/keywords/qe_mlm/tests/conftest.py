import spacy
import pytest

from gamechangerml.src.featurization.keywords.qe_mlm.qe import QeMLM


@pytest.fixture(scope="session")
def qe_mlm():
    nlp = spacy.load("en_core_web_md")
    qe = QeMLM(nlp, model_path="bert-base-uncased")
    return qe
