import logging
import pickle
import re
from collections import defaultdict

import numpy as np
from spacy.vocab import Vocab

from gamechangerml.src.search.query_expansion.sif_alg import sif_embedding
from gamechangerml.src.utilities.np_utils import is_zero_vector
from gamechangerml.src.utilities.np_utils import l2_norm_vector

logger = logging.getLogger(__name__)

abbrv_re = re.compile("\\(([A-Za-z0-9\\&\\-/]+)\\)")
spacy_vocab = Vocab()


def correct_lf(lf):
    lf_ = re.sub(re.escape("- "), "-", lf)
    return lf_.strip()


def load_abbrv_dict(abbrv_path):
    logger.info(abbrv_path)
    try:
        with open(abbrv_path, "rb") as ap:
            ab_dict = pickle.load(ap)
        return ab_dict
    except FileNotFoundError as e:
        raise e


def contains_abbrv(sf, lf, next_pass):
    m_obj = abbrv_re.search(lf)
    if m_obj is not None:
        next_pass[sf].append(lf)
        return True
    else:
        return False


def embed_abbreviations_1(
    abbrv_path, word_wt, nlp, raw_abrv_dict=None, abrv_vector_dict=None
):
    if raw_abrv_dict is None:
        pass_ = 1
        logger.info("loading {}".format(abbrv_path))
        raw_abrv_dict = load_abbrv_dict(abbrv_path)
    else:
        logger.info("starting with {:,}".format(len(raw_abrv_dict)))
        pass_ = 2

    short_forms = set(raw_abrv_dict.keys())
    logger.info("num abbreviations : {:,}".format(len(short_forms)))

    next_pass = defaultdict(list)
    if abrv_vector_dict is None:
        abrv_vector_dict = dict()
    sif_matrix = list()
    for short_form, long_forms in raw_abrv_dict.items():
        if len(short_form) == 1:
            continue
        for lf in long_forms:
            lf_ = correct_lf(lf)
            if pass_ == 1 and contains_abbrv(
                short_form, lf_.lower(), next_pass
            ):
                logger.info(
                    "pass {} contains abbrv {}: {}".format(
                        pass_, short_form, lf
                    )
                )
                continue
            else:
                if not lf_:
                    logger.warning(
                        "pass {} empty: {} {}".format(pass_, short_form, lf_)
                    )
                    continue
                sif_vector = sif_embedding(
                    lf.lower(), nlp, word_wt, strict=False
                )
                sif_matrix.append(sif_vector)

        # simple average of SIF embeddings followed by an L2 norm
        if len(sif_matrix) == 0:
            continue
        sif_matrix_ = np.array(sif_matrix, dtype=np.float32)
        sif_avg = sif_matrix_.sum(axis=0) / np.float32(sif_matrix_.shape[0])
        if is_zero_vector(sif_avg):
            logger.warning(
                "pass {} could not embed {:>10s}".format(pass_, short_form)
            )
            continue
        logger.info(
            "pass {} embedding {:>10s} : {}".format(
                pass_, short_form, sif_matrix_.shape
            )
        )
        abrv_vector_dict[short_form.lower()] = l2_norm_vector(sif_avg)
        del sif_matrix[:]

    if pass_ == 2:
        add_to_spacy(abrv_vector_dict)
    return abrv_vector_dict, next_pass


def embed_abbreviations_2(
    abbrv_path, word_wt, nlp, next_pass, abrv_vector_dict
):
    logger.info(
        "-- pass 2 of abbreviation embedding {:,} --".format(len(next_pass))
    )
    final_vector_dict, left_overs = embed_abbreviations_1(
        abbrv_path, word_wt, nlp, next_pass, abrv_vector_dict
    )
    logger.info("final vector len {:,}".format(len(final_vector_dict)))
    logger.info("num leftovers (could not embed) : {}".format(len(left_overs)))
    logger.info("{}".format(nlp("reporting system").similarity(nlp("drs"))))
    return final_vector_dict, left_overs


def add_to_spacy(word_vec_dict):
    logger.info("adding {:,} vectors to spaCy".format(len(word_vec_dict)))
    for word, vector in word_vec_dict.items():
        spacy_vocab.set_vector(word, vector)
