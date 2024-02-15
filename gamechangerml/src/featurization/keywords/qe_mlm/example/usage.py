import logging
from pprint import pformat

import spacy

from gamechangerml.src.featurization.keywords.qe_mlm.qe import QeMLM

logger = logging.getLogger(__name__)


def ex_1(query, qe):
    res = qe.predict(query, threshold=0.2, top_n=2)
    logger.info("query     : {}".format(query))
    logger.info("expansion : {}".format(res))
    logger.info("explain")
    logger.info(pformat(qe.explain, indent=2, width=80))


if __name__ == "__main__":
    fmt = (
        "[%(asctime)s %(levelname)-8s] "
        + "[%(filename)s:%(lineno)4s - %(funcName)s()] %(message)s"
    )
    logging.basicConfig(level=logging.INFO, format=fmt)

    queries = [
        "passport",
        "Find a book, painting, or work of art created in Santa Monica or on the west coast",  # noqa
        "telework policy for remote work",
    ]

    logger.info("loading all models...")
    nlp = spacy.load("en_core_web_md")
    qe_ = QeMLM(nlp, model_path="bert-base-uncased")
    logger.info("loaded")

    for q in queries:
        ex_1(q, qe_)
