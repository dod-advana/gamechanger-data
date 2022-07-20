import logging
import os
import pickle

import numpy as np
from annoy import AnnoyIndex
import spacy

import gamechangerml.src.search.query_expansion.version_ as v
from gamechangerml.src.search.query_expansion.sif_alg import sif_embedding
from gamechangerml.src.search.query_expansion.utils import (
    find_ann_indexes,
    QEConfig,
    angular_dist_to_cos,
)
from gamechangerml.src.search.query_expansion.word_wt import get_word_weight
from gamechangerml.src.utilities.np_utils import is_zero_vector
from gamechangerml.src.utilities.spacy_model import (
    get_lg_vectors,
    spacy_vector_width,
)

# commenting out unused and due to tensorflow issue in prod 12/18/20
# from gamechangerml.src.featurization.keywords.qe_mlm.qe import QeMLM
from gamechangerml.src.utilities.timer import Timer

logger = logging.getLogger(__name__)


class QE(object):
    __version__ = v.__version__

    def __init__(self, qe_model_dir, qe_files_dir, method):
        """
         Query expansion via smoothed inverse frequency weighted word embeddings
         and approximate nearest neighbor search.

          Args:
              qe_model_dir (str|None): Path where the query expansion indexes
                  reside; These are prefixed with `ann-index_` and
                  `ann-index-vocab_`. These carry a timestamp in their names. If
                  the timestamps do not match, an exception is raised.

              method (str): If "emb", use GloVe to embed the user query and find
                  the 'most similar' vectors/keywords using a pre-built ANN
                  index. If "mlm", use a BERT-based masked language model to
                  find expansion words.
        Query expansion via smoothed inverse frequency weighted word embeddings
        and approximate nearest neighbor search.
        """
        logger.info("{} version {}".format(
            self.__class__.__name__, self.__version__))
        self.method = method
        self.empty = np.array([0.0])
        self._alpha = 1e-03
        self.qe_files_dir = qe_files_dir
        np.set_printoptions(precision=2)

        try:
            if self.method == "mlm":
                raise NotImplementedError(
                    "MLM method is not implemented currently.")

                # logger.info("loading models for {}".format(self.method))
                # self.spacy_nlp = spacy.load("en_core_web_md")
                # self.qe_mlm = QeMLM(
                #    spacy_nlp=self.spacy_nlp, model_path="bert-base-uncased"
                # )
            elif self.method == "emb":
                logger.info("loading models for {}".format(self.method))
                self._setup_emb(qe_model_dir)
            else:
                raise ValueError("unknown method: {}".format(self.method))

        except (OSError, FileNotFoundError) as e:
            logger.exception("{}: {}".format(type(e), str(e)), exc_info=True)

    def _setup_emb(self, qe_model_dir):
        cfg = QEConfig()
        #here = os.path.dirname(os.path.realpath(__file__))
        #wt_path = os.path.join(self.qe_files_dir, "aux_data", vocab_file)

        try:
            ann_file, vocab_file = find_ann_indexes(qe_model_dir)
            self._nlp = get_lg_vectors()
            self.word_wt = get_word_weight(a=self._alpha)

            logger.info("loading QE indexes")
            vector_dim = spacy_vector_width(self._nlp)
            self._ann = AnnoyIndex(vector_dim, cfg.embedding_dist)
            self._ann.load(ann_file)

            with open(vocab_file, "rb") as fh:
                self._vocab = pickle.load(fh)
                assert type(self._vocab) is list
                logger.info(
                    "QE vocabulary size : {:,}".format(len(self._vocab)))
        except (FileNotFoundError, Exception) as e:
            raise e

    def _similar_to(self, query_str, topn, threshold):
        expanded = list()

        q_vec = sif_embedding(query_str, self._nlp, self.word_wt, strict=True)
        if is_zero_vector(q_vec):
            return expanded
        try:
            v_idx, dist = self._ann.get_nns_by_vector(
                q_vec, topn + 1, search_k=-1, include_distances=True
            )
            cos_ = angular_dist_to_cos(dist)
            expanded = [
                self._vocab[idx]
                for j_idx, idx in enumerate(v_idx)
                if cos_[j_idx] > threshold
                if self._vocab[idx].strip() != query_str.lower().strip()
            ]
            final_cos = np.array([cos_[idx] for idx in range(len(expanded))])
            logger.debug("{}".format(query_str.lower().strip()))
            logger.debug(" cos sim {}".format(final_cos))
            logger.debug("expanded {}".format(expanded))
            # logger.debug("   vocab {}".format(
            #     [self._vocab[idx] for idx in v_idx]))
            return expanded[:topn]
        except IndexError as e:
            logger.exception("{}: {}".format(type(e), str(e)), exc_info=True)
            raise

    def expand(self, query_str, topn, threshold, min_tokens):
        """
        Expands a query string into the `topn` most similar terms excluding
        the tokens in `query_str`. If a token does not have an embedding,
        it is not added to the embedding matrix.

        Args:
            query_str (str): query string

            topn (int): number of most similar terms

            threshold (float): if the method is "mlm", the softmax probability
                must be > threshold for a word to included in the expansion

            min_tokens (int): if the method is "mlm", the number of tokens in
                the `query_str` must be > `min_tokens`; this value is ignored
                if `method="emb"`.

        Returns:
            list of up to `topn` most similar terms if an embedding exists
                for `query_str`. Empty list indicates no expansion terms are
                available.

        """
        expansion_terms = list()
        with Timer():
            if not query_str:
                logger.warning("query string is empty")
                return expansion_terms
            if self.method == "emb":
                expansion = self._similar_to(query_str, topn, threshold)
            elif self.method == "mlm":
                expansion = self.qe_mlm.predict(
                    query_str,
                    top_n=topn,
                    threshold=threshold,
                    min_tokens=min_tokens,
                )
        return expansion
