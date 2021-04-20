from gensim.models.tfidfmodel import TfidfModel
from gensim import corpora
import os
import logging

logger = logging.getLogger("gamechanger")


class Topics(object):
    """
    TF-iDF topic model wrapper class.

    This class is written to be processing pipeline egnostic, but
    because of that be sure that you track your own pipeline for
    training and inference otherwise results may vary.

    Also note that this class will allow you to perform topic modeling
    on out of corpus documents.  Be sure to monitor the number of
    documents being processed out of corpus to ensure that the model
    still reflects the statistics of the corpus.  When this is no longer
    the case you can either retrain from scatch. TODO: Implement an
    update function to update the model on only the new documents.

    Class requirements:
        from gensim.models.tfidfmodel import TfidfModel
        from gensim import corpora
    """

    def __init__(self, directory=None, verbose=False):
        try:
            if directory is not None:
                self.load(directory)
        except Exception as e:
            logger.warning("Could not load topics model")
            logger.warning(e)
        if verbose:
            try:
                logging.basicConfig(
                    format="%(asctime)s : %(levelname)s : %(message)s",
                    level=logging.INFO,
                )
            except:
                import logging

                logging.basicConfig(
                    format="%(asctime)s : %(levelname)s : %(message)s",
                    level=logging.INFO,
                )
        else:
            try:
                logging.basicConfig(
                    format="%(asctime)s : %(levelname)s : %(message)s",
                    level=logging.ERROR,
                )
            except:
                pass

    def load(self, directory):
        """
        load - class function to load the required files from a
            directory.
        Args:
            directory (str): Path to where `tfidf_dictionary.dic`
                and `tfidf.model` are located.
        Returns:
            None
        """
        dictionary_path = os.path.join(directory, "tfidf_dictionary.dic")
        tfidf_path = os.path.join(directory, "tfidf.model")
        self.dictionary = corpora.Dictionary.load(dictionary_path)
        self.tfidf = TfidfModel.load(tfidf_path)

    def save(self, directory):
        """
        save - class function to save a dictionary file and the
            tfidf model file from a training.
        Args:
            directory (str): Path to where `tfidf_dictionary.dic`
                and `tfidf.model` will be saved.  Ensure that
                there are not versions of these files in `directory`
                before saving or they will be overwritten.
        Returns:
            None
        """
        dictionary_path = os.path.join(directory, "tfidf_dictionary.dic")
        tfidf_path = os.path.join(directory, "tfidf.model")

        self.dictionary.save(dictionary_path)
        self.tfidf.save(tfidf_path)

    def train(self, corpus):
        """
        train - Train a TF-iDF model on a corpus
        Args:
            corpus (iterable): An iterable where each element is a list of
                tokens.
        Returns:
            None
        """
        self.dictionary = corpora.Dictionary(corpus)
        doc_term_matrix = [self.dictionary.doc2bow(doc) for doc in corpus]
        self.tfidf = TfidfModel(doc_term_matrix)

    def get_topics(self, tokens, topn=5):
        """
        get_topics - given a tokenized text, get a list of the topn topics
            with their scores
        Args:
            tokens (list): A tokenized text list.
            topn (int): the number of topic to be returned
        Returns:
            topics (list|tuple): a list of (score, topic) pairs
        """
        doc_term_matrix = [self.dictionary.doc2bow(tokens)]
        doc_tfidf = self.tfidf[doc_term_matrix]

        word = []
        doc = doc_tfidf[0]
        for id, value in doc:
            word.append((value, self.dictionary.get(id)))
        word.sort(reverse=True)
        return word[:topn]
