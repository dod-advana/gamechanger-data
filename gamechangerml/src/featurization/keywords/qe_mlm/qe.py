#
# MIT License
#
# Copyright (c) 2020 Victor Dibia, Chris Skiscim
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
import logging
from operator import itemgetter

import spacy
import tensorflow as tf
from transformers import AutoTokenizer, TFBertForMaskedLM

import gamechangerml.src.featurization.keywords.qe_mlm.version as v

logger = logging.getLogger(__name__)


def count_words(text):
    wc = text.count(" ")
    return wc + 1


class QeMLM(object):
    __version__ = v.__version__

    def __init__(self, spacy_nlp=None, model_path="bert-base-uncased"):
        """
        Masked language model for query expansion. The contextual query
        expansion algorithm is described in
        https://arxiv.org/pdf/2007.15211.pdf. This implementation uses
        Tensorflow.

        Args:
            spacy_nlp (spacy.lang.en.English): instantiated spaCy language
                model; note this must have the default pipeline components
                `["tagger", "ner"]`

            model_path (str): name or path of the Hugging Face `transformer`
                model

        Raises:
            AttributeError: if the spacy pipeline does not have the required
                processing components

            OSError: if the specified `model_name` cannot be loaded
        """
        self.nlp = spacy_nlp
        self.model_path = model_path

        self.req_pipeline = ["tagger", "ner"]
        self.candidate_pos = ["NOUN", "ADJ", "ADV"]

        nlp_pipeline = self.nlp.meta["pipeline"]
        chk = [component in nlp_pipeline for component in self.req_pipeline]
        if False in chk:
            raise AttributeError(
                "spaCy pipeline must be {}; got {}".format(
                    self.req_pipeline, nlp_pipeline
                )
            )

        logger.info("loading {}".format(model_path))
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_path, use_fast=True
            )
            self.model = TFBertForMaskedLM.from_pretrained(
                self.model_path, from_pt=True
            )
        except OSError as e:
            raise e

        self._result = None
        logger.info("{} {}".format(self.__class__.__name__, self.__version__))

    @property
    def explain(self):
        """
        Return detailed data concerning the current query and its expansion

        Returns:
            dict: See `_predict_mask()` for details
        """
        return self._result

    @staticmethod
    def _predict_mask(sequence, model, tokenizer, top_n=2):
        input_ = tokenizer.encode(sequence, return_tensors="tf")
        mask_token_index = tf.where(input_ == tokenizer.mask_token_id)[0, 1]
        token_logits = model(input_)[0]
        mask_token_logits = token_logits[0, mask_token_index, :]

        probs = tf.nn.softmax(mask_token_logits)
        topk = tf.math.top_k(probs, top_n)
        top_n_probs, top_n_tokens = topk.values.numpy(), topk.indices.numpy()
        results = [
            {
                "token": tokenizer.decode([top_n_tokens[i]]),
                "probability": float(top_n_probs[i]),
            }
            for i in range(len(top_n_probs))
        ]
        return results

    def _expand(self, query, top_n, threshold, min_tokens):
        new_terms = list()
        candidate_expansions = list()

        wc = count_words(query)
        if wc < min_tokens:
            logger.warning(
                "number of tokens {} < min_tokens {}".format(wc, min_tokens)
            )
            return candidate_expansions

        doc = self.nlp(query)
        query_tokens = [token.orth_ for token in doc]

        for i, token in enumerate(doc):
            pred_tokens = None
            if token.pos_ in self.candidate_pos and not token.ent_type_:
                temp_doc = query_tokens.copy()
                temp_doc[i] = self.tokenizer.mask_token
                temp_doc = " ".join(temp_doc)
                pred_tokens = self._predict_mask(
                    temp_doc, self.model, self.tokenizer, top_n=top_n
                )
                new_terms = new_terms + pred_tokens
            candidate_expansions.append(
                {
                    "token": token.orth_,
                    "expansion": pred_tokens,
                    "token_index": i,
                    "pos": token.pos_,
                    "pos_desc": spacy.explain(token.pos_),
                    "named_entity": token.ent_type_,
                    "ent_desc": spacy.explain(token.ent_type_),
                }
            )

        terms_list = list()
        seen_terms = set()
        for token in new_terms:
            if (
                token["token"].isalnum()
                and token["probability"] > threshold
                and "#" not in token["token"]
                and token["token"] not in query
                and token["token"] not in seen_terms
            ):
                terms_list.append(token)
                seen_terms.add(token["token"])

        self._result = {
            "terms": terms_list,
            "query": query_tokens,
            "expansions": candidate_expansions,
        }
        return terms_list

    def predict(self, query, top_n=3, threshold=0.2, min_tokens=3):
        """
        Find a list of expansion terms for the given `query`. For each query
        token satisfying the part-of-speech filter. Mask and then predict the
        `top_n` tokens for the mask. A token is considered as an expansion
        term if the softmax probability > `threshold`.

        Args:
            query (str): user query

            top_n (int): number of expansion terms to return

            threshold (float): used as described above to limit an acceptable
                expansion

            min_tokens (int): number of query tokens must exceed this to be
                considered for prediction

        Returns:
            List(str): `top_n` expansion terms ordered by probability

        """
        result = self._expand(query, top_n, threshold, min_tokens)
        result = sorted(result, key=itemgetter("probability"), reverse=True)
        return [r["token"] for r in result][:top_n]
