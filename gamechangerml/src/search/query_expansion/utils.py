import logging
import os
import time

import numpy as np

from gamechangerml.src.utilities.np_utils import is_zero_vector

logger = logging.getLogger(__name__)


class QEConfig:
    def __init__(self):
        self._childDocuments_ = "_childDocuments_"
        self.id_ = "id"
        self.NA = "NA"
        self.type_ = "type"
        self.page_ = "page"
        self.p_raw_text_ = "p_raw_text"
        self.index_prefix = "ann-index_"
        self.index_ext = ".ann"
        self.vocab_prefix = "ann-index-vocab_"
        self.vocab_ext = ".pkl"
        self.embedding_dist = "angular"
        self.index_attribs = (
            self.index_prefix,
            self.index_ext,
            self.vocab_prefix,
            self.vocab_ext,
        )


cfg = QEConfig()


def remove_original_kw(
    expansion_list,
    term,
):
    """remove_original_kw: removes original keyword from the expanded term
    Args:
        expansion_list: list; expanded words
    Returns:
        finalTerms: list; expanded words with original kw removed
    """
    finalTerms = []
    for words in expansion_list:
        split_terms = words.split(" ")
        tmpList = [x for x in split_terms if x != term]
        tmpList = [" ".join(tmpList)]
        finalTerms = finalTerms + tmpList
    return finalTerms


def _check_idx_timestamps(ann_file, vocab_file):
    ann_base, ext = os.path.splitext(os.path.basename(ann_file))
    vocab_base, ext = os.path.splitext(os.path.basename(vocab_file))
    ann_ts = ann_base.split("_")[-1]
    vocab_ts = vocab_base.split("_")[-1]
    if ann_ts != vocab_ts:
        msg = "index and vocabulary timestamps do not match; " + "got {} and {}".format(
            ann_base, vocab_base
        )
        logger.fatal(msg)
        raise AttributeError(msg)
    else:
        ann_ts = time.strftime("%Y-%m-%d %H:%M:%S",
                               time.localtime(float(ann_ts)))
        logger.info("QE model timestamp : {}".format(ann_ts))


def find_ann_indexes(model_dir):
    anns = list()
    vocabs = list()
    for index_file in sorted(os.listdir(model_dir)):
        if (cfg.index_prefix in index_file) and index_file.endswith(cfg.index_ext):
            anns.append(index_file)
        if (cfg.vocab_prefix in index_file) and index_file.endswith(cfg.vocab_ext):
            vocabs.append(index_file)

    if len(anns) != 1 or len(vocabs) != 1:
        msg = (
            "there must be one index and one vocabulary present. "
            + "got {} and {} in {}".format(anns, vocabs, model_dir)
        )
        logger.fatal(msg)
        raise ValueError(msg)
    else:
        ann_file = os.path.join(model_dir, anns[0])
        vocab_file = os.path.join(model_dir, vocabs[0])
        _check_idx_timestamps(ann_file, vocab_file)
    return ann_file, vocab_file


def check_vecs(vectors):
    chk = [is_zero_vector(v) for v in vectors]
    if True in chk:
        raise ValueError("all zero vector {}".format(chk))


def angular_dist_to_cos(vector):
    v = np.clip(vector, -1.0, 1.0)
    return np.arccos(v) / np.pi
