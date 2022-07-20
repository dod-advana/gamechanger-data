import json
import logging
import os

import spacy

from gamechangerml.src.search.query_expansion.sif_alg import sif_embedding
from gamechangerml.src.search.query_expansion.word_wt import get_word_weight
from gamechangerml.src.utilities.np_utils import is_zero_vector
from gamechangerml.src.utilities.numpy_encoder import NumpyEncoder
from gamechangerml.src.utilities.text_generators import gen_json_mult_keys
from gamechangerml.src.utilities.timer import Timer
from gamechangerml import DATA_PATH

logger = logging.getLogger(__name__)


def embed_titles(corpus_dir, nlp, word_wt):
    title_count = 0
    skipped = 0
    oov = 0
    embed_dict = dict()
    keys = ("title", "filename")
    with Timer():
        for values in gen_json_mult_keys(corpus_dir, keys=keys):
            title, filename = values
            filename, _ = os.path.splitext(filename)
            if title in filename:
                skipped += 1
                continue
            sif_vector = sif_embedding(
                title.lower(), nlp, word_wt, strict=False
            )
            if is_zero_vector(sif_vector):
                oov += 1
            title_count += 1
            if title_count in [1, 5, 10, 100, 500] or title_count % 1000 == 0:
                logger.info("titles processed {:>6,d}".format(title_count))
            embed_dict[filename] = sif_vector
        logger.info("total processed {:>6,d}".format(title_count))
        logger.info("        skipped {:>6,d}".format(skipped))
        logger.info("   out of vocab {:>6,d}".format(oov))
        logger.info("     total used {:>6,d}".format(len(embed_dict)))
        json_out = make_json(embed_dict)
    return json_out


def make_json(word_vec_dict):
    json_dict = dict()
    for word, vector in word_vec_dict.items():
        json_dict[word] = json.dumps(vector, cls=NumpyEncoder)
    json_out = json.dumps(json_dict)
    return json_out


if __name__ == "__main__":
    log_fmt = (
        "[%(asctime)s %(levelname)-8s], [%(filename)s:%(lineno)s - "
        + "%(funcName)s()], %(message)s"
    )
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    logger.info("loading spaCy")
    nlp = spacy.load("en_core_web_lg")
    logger.info("spaCy loaded")

    c_dir = (
        "/Users/chrisskiscim/projects/gamechanger/repo/corpus_json_20201101"
    )
    ww = os.path.join(
        DATA_PATH,
        "features", "word-freq-corpus-20201101.txt"
    )
    word_wt_file = os.path.join(
        DATA_PATH,
        "features", "word-freq-corpus-20201101.txt"
    )
    word_weights = get_word_weight(word_wt_file)
    embed_titles(c_dir, nlp, word_weights)
