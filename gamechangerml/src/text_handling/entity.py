import os
from gensim.models.phrases import Phraser, Phrases
import logging

logger = logging.getLogger("gamechanger")


class Phrase_Detector(object):
    """
    This class acts as a wrapper around 2 iterations of Gensim's
    Phraser object, which allows for bigrams, trigrams and
    quadgrams to be applied.
    """

    def __init__(self, model_id):
        self.__bigram_model__ = None
        self.__trigram_model__ = None
        self.model_id = model_id

    def __get_bigram_model__(self):
        return self.__bigram_model__

    def __get_trigram_model__(self):
        return self.__trigram_model__

    def __set_bigram_model__(self, model):
        self.__bigram_model__ = model

    def __set_trigram_model__(self, model):
        self.__trigram_model__ = model

    def train(self, corpus, min_count=10):
        logger.info("Training bigram")
        """
        params:
            corpus - a generator that returns lists of strings
            min_count - min number of times a phrase needs to
                appear in the corpus to be considered for
                phrase detection
        return:
            No return
        """
        logger.info("Training bigram")
        phrases = Phrases(corpus, min_count=min_count)
        bigram = Phraser(phrases)
        self.__set_bigram_model__(bigram)
        logger.info("Training trigram")
        phrases = Phrases(bigram[corpus], min_count=min_count)
        trigram = Phraser(phrases)
        self.__set_trigram_model__(trigram)

    def load(self, ngram_dir):
        """
        This function will sort the contents of ngram_dir and select
            the bigram and trigram models that appear first
        params:
            ngram_dir - must be a directory that contains the bigram
                and trigram models.
        returns:
            No Returns
        """
        files = os.listdir(ngram_dir)
        files.sort()
        files = [f for f in files if ".phr" in f]
        bigram = Phraser.load(os.path.join(ngram_dir, files[0]))
        self.__set_bigram_model__(bigram)
        trigram = Phraser.load(os.path.join(ngram_dir, files[1]))
        self.__set_trigram_model__(trigram)

    def save(self, save_ngram_dir):
        """
        params:
            save_ngram_dir - must be a directory for the bigram and
                trigram models to be saved
            model_id - a unique identifier that will be prepended to
                the model.  Ideally this should be a datetime stamp.
        returns:
            No Returns
        """
        self.__get_bigram_model__().save(
            os.path.join(
                save_ngram_dir, f"{self.model_id}/{self.model_id}_bigram.phr"
            )
        )
        self.__get_trigram_model__().save(
            os.path.join(
                save_ngram_dir, f"{self.model_id}/{self.model_id}_trigram.phr"
            )
        )

    def apply(self, text_list):
        """
        params:
            text_list - a list of strings
        returns:
            a list of strings
        """
        bigram = self.__get_bigram_model__()
        trigram = self.__get_trigram_model__()
        return trigram[bigram[text_list]]
