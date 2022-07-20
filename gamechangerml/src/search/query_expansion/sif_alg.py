import numpy as np
import logging
import spacy


from gamechangerml.src.utilities.np_utils import l2_norm_vector, is_zero_vector

logger = logging.getLogger(__name__)

zero_array = np.array([0.0])


def _embedding(token_in):
    vector = token_in.vector
    oov = np.all(vector == 0.0)
    return vector, oov


def sif_embedding(query_str, nlp, word_wt, strict=False):
    q_lower = query_str.strip().lower()
    if not q_lower:
        logger.warning("empty text")
        return zero_array

    wt_matrix = list()
    tokens = list()
    token_objs = [t for t in nlp(q_lower)]

    if len(token_objs) == 1:
        embed = (token_objs[0]).vector
        return embed

    for t in token_objs:
        if t.is_space:
            continue
        vec, oov = _embedding(t)
        if oov:
            # logger.warning(
            #     "out of vocabulary : {:25s}  {}".format(t.text, query_str)
            # )
            if strict:
                # logger.warning("returning zero vector for {}".format(t.orth_))
                return zero_array
        if t in word_wt:
            wt = word_wt[t.lower_]
        else:
            wt = 1.0
        wt_matrix.append(vec * wt)
        tokens.append(t)

    if wt_matrix:
        wt_mtx_ = np.array(wt_matrix)
        avg_vec = wt_mtx_.sum(axis=0) / np.float32(wt_mtx_.shape[0])
        if is_zero_vector(avg_vec):
            return zero_array
        normed_vec = l2_norm_vector(avg_vec)
        return normed_vec
    else:
        return zero_array
