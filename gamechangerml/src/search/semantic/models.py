import os
import logging
from gensim.models.doc2vec import Doc2Vec
from datetime import datetime
from collections import defaultdict
from gamechangerml.src.utilities.utils import save_all_s3
import multiprocessing

logger = logging.getLogger("gamechanger")

default_model_args = {
    "dm": 0,
    "dbow_words": 1,
    "vector_size": 100,
    "window": 5,
    "min_count": 5,
    "sample": 1e-5,
    "epochs": 25,
    "alpha": 0.025,
    "min_alpha": 0.005,
    "workers": 3
    * multiprocessing.cpu_count()
    // 4,  # to allow some portion of the cores to perform generator tasks
}


class D2V(object):
    def __init__(self, model_id):
        self.model = None
        self.model_id = model_id

    def train(self, model_args, tagged_corpus):
        self.model = Doc2Vec(**model_args)

        logger.info("Building model vocabulary.  This can be time consuming.")
        self.model.build_vocab(tagged_corpus)

        logger.info("Training model. This can be time consuming.")
        self.model.train(
            tagged_corpus,
            total_examples=self.model.corpus_count,
            epochs=self.model.epochs,
        )

    def save(self, directory, save_remote):
        """
        Args:
            directory - must be a directory for the model to be saved
            model_id - a unique identifier that will be prepended to
                the model.  Ideally this should be a datetime stamp.
        Returns:
            No Returns
        """
        assert self.model != None, "No model currently in D2V instance"

        fullname = f"{self.model_id}/{self.model_id}_model.d2v"
        file_name = os.path.join(directory, fullname)
        logger.info(f"Saving trained model as {file_name}.")
        self.model.save(file_name)
        if save_remote:
            save_all_s3(directory, self.model_id)

    def load(self, file_path):
        """
        Args:
            file_path - path to a Doc2Vec model to be loaded
        Returns:
            No Returns
        """
        self.model_id = file_path.split("/")[-1].split("_")[0]
        self.model = Doc2Vec.load(file_path)

    def infer(self, tokenized_text, num_docs=10, max_para=5):
        """
        Args:
            tokenized_text (list): a list of strings
            num_docs (int): number of documents that will be returned
            max_para (int): max number of paragraphs within a doc
                            that will be returned

        Yields:
            child document text (str), file name (str), doc id (str)
        """
        assert self.model != None, "No model currently in D2V instance"
        assert (
            type(tokenized_text) == list
        ), "infer() input must be list--a tokenized str"

        topn = 50
        if len(tokenized_text) == 1:
            try:
                # try to pull the stored word vector
                vec = self.model.wv.word_vec(tokenized_text[0])
            except:
                return {}  # the word is not in the vocab, so return
                # results would be a waste
        else:
            vec = self.vectorize(tokenized_text)

        sim = self.model.docvecs.most_similar([vec], topn=topn)
        sim = self._format_returns(sim, num_docs, max_para)
        while len(sim) < num_docs:
            topn += 50
            sim = self.model.docvecs.most_similar([vec], topn=topn)
            sim = self._format_returns(sim, num_docs, max_para)
            # needs to be a max or stuck in a loop
            if topn == (num_docs * 50):
                break
        return sim

    def get_corpus_list(self):
        assert self.model != None, "No model currently in D2V instance"

        return list(self.model.docvecs.doctags)

    def vectorize(self, tokenized_text):
        self.model.random.seed(123)
        vec = self.model.infer_vector(
            tokenized_text,
            alpha=self.model.alpha,
            min_alpha=self.model.min_alpha,
            epochs=self.model.epochs,
        )
        return vec

    def _format_returns(self, sim, num_docs, max_para):
        """
        Args:
            sim (list): a list of tuples, with index 0 being an id, and index 1 being a cosine similarity
        Returns:
            defaultdict(list): keys are the the document ids (str)
                               values are a list of tuples: (paragraph #, cosine similarity)
        """
        result_dict = defaultdict(list)
        num_docs_count = 0
        for element, score in sim:
            element = element.split("_")
            doc_id = "_".join(element[:-1])
            paragraph_num = element[-1]
            if num_docs_count < num_docs or doc_id in result_dict:
                if len(result_dict[doc_id]) < max_para:
                    result_dict[doc_id].append((paragraph_num, score))
            num_docs_count = len(result_dict)
        return result_dict
