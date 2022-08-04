import os
from gamechangerml.src.search.QA.QAReader import DocumentReader as QAReader
from gamechangerml.configs import (
    QAConfig,
    EmbedderConfig,
    DocCompareEmbedderConfig,
    SimilarityConfig,
    DocCompareSimilarityConfig,
    QexpConfig,
    TopicsConfig,
)
from gamechangerml.src.search.query_expansion import qe
from gamechangerml.src.search.sent_transformer.model import (
    SentenceSearcher,
    SentenceEncoder,
)
from gamechangerml.src.search.doc_compare import (
    DocCompareSentenceEncoder,
    DocCompareSentenceSearcher,
)
from gamechangerml.src.recommender.recommend import Recommender
from gamechangerml.src.search.embed_reader import sparse
from gamechangerml.api.fastapi.settings import (
    logger,
    TOPICS_MODEL,
    MODEL_LOAD_FLAG,
    QEXP_JBOOK_MODEL_NAME,
    QEXP_MODEL_NAME,
    WORD_SIM_MODEL,
    LOCAL_TRANSFORMERS_DIR,
    SENT_INDEX_PATH,
    DOC_COMPARE_SENT_INDEX_PATH,
    latest_intel_model_encoder,
    latest_intel_model_sim,
    latest_intel_model_trans,
    latest_doc_compare_sim,
    latest_doc_compare_encoder,
    QA_MODEL,
)
from gamechangerml.src.featurization.word_sim import WordSim
from gamechangerml.src.featurization.topic_modeling import Topics
from gamechangerml.api.utils import processmanager

# A singleton class that loads all of the models.
# All variables and methods are static so you
# reference them by ModelLoader().example_method()


class ModelLoader:
    # private model variables
    def __init__(self):
        __qa_model = None
        __sentence_searcher = None
        __sentence_encoder = None
        __query_expander = None
        __query_expander_jbook = None
        __word_sim = None
        __sparse_reader = None
        __topic_model = None
        __recommender = None
        __document_compare_searcher = None
        __document_compare_encoder = None

    # Get methods for the models. If they don't exist try initializing them.
    def getQA(self):
        if ModelLoader.__qa_model == None:
            logger.warning(
                "qa_model was not set and was attempted to be used. Running init"
            )
            ModelLoader.initQA()
        return ModelLoader.__qa_model

    def getQE(self):
        if ModelLoader.__query_expander == None:
            logger.warning(
                "query_expander was not set and was attempted to be used. Running init"
            )
            ModelLoader.initQE()
        return ModelLoader.__query_expander

    def getQEJbook(self):
        if ModelLoader.__query_expander_jbook == None:
            logger.warning(
                "query_expander was not set and was attempted to be used. Running init"
            )
            ModelLoader.initQEJBook()
        return ModelLoader.__query_expander_jbook

    def getWordSim(self):
        if ModelLoader.__word_sim == None:
            logger.warning(
                "word_sim was not set and was attempted to be used. Running init"
            )
            # ModelLoader.initWordSim()
        return ModelLoader.__word_sim

    def getSentence_searcher(self):
        if ModelLoader.__sentence_searcher == None:
            logger.warning(
                "sentence_searcher was not set and was attempted to be used. Running init"
            )
            ModelLoader.initSentenceSearcher()
        return ModelLoader.__sentence_searcher

    def getSentence_encoder(self):
        if ModelLoader.__sentence_encoder == None:
            logger.warning(
                "sentence_encoder was not set and was attempted to be used. Running init"
            )
            ModelLoader.initSentenceEncoder()
        return ModelLoader.__sentence_encoder

    def getDocumentCompareSearcher(self):
        if ModelLoader.__document_compare_searcher == None:
            logger.warning(
                "document_compare_searcher was not set and was attempted to be used. Running init"
            )
            ModelLoader.initDocumentCompareSearcher()
        return ModelLoader.__document_compare_searcher

    def getDocumentCompareEncoder(self):
        if ModelLoader.__document_compare_encoder == None:
            logger.warning(
                "document_compare_encoder was not set and was attempted to be used. Running init"
            )
            ModelLoader.initDocumentCompareEncoder()
        return ModelLoader.__document_compare_encoder

    def getSparse(self):
        return ModelLoader.__sparse_reader

    def getTopicModel(self):
        if ModelLoader.__topic_model is None:
            logger.warning(
                "topic_model was not set and was attempted to be used. Running init"
            )
            ModelLoader.initTopics()
        return ModelLoader.__topic_model

    def getRecommender(self):
        if ModelLoader.__recommender is None:
            logger.warning(
                "recommender was not set and was attempted to be used. Running init"
            )
            ModelLoader.initRecommender()
        return ModelLoader.__recommender

    def set_error(self):
        logger.error("Models cannot be directly set. Must use init methods.")

    # Static variables that use these custom getters defined above.
    # So when ModelLoader().qa_model is referenced getQA is called.
    qa_model = property(getQA, set_error)
    query_expander = property(getQE, set_error)
    query_expander_jbook = property(getQEJbook, set_error)
    sparse_reader = property(getSparse, set_error)
    sentence_searcher = property(getSentence_searcher, set_error)
    sentence_encoder = property(getSentence_encoder, set_error)
    word_sim = property(getWordSim, set_error)
    topic_model = property(getTopicModel, set_error)
    recommender = property(getRecommender, set_error)
    document_compare_searcher = property(getDocumentCompareSearcher, set_error)
    document_compare_encoder = property(getDocumentCompareEncoder, set_error)

    @staticmethod
    def initQA(qa_model_name=QA_MODEL.value):
        """initQA - loads transformer model on start
        Args:
        Returns:
        """
        try:
            logger.info("Starting QA pipeline")
            ModelLoader.__qa_model = QAReader(
                transformer_path=LOCAL_TRANSFORMERS_DIR.value,
                use_gpu=True,
                model_name=qa_model_name,
                **QAConfig.MODEL_ARGS,
            )
            # set cache variable defined in settings.py
            QA_MODEL.value = ModelLoader.__qa_model.READER_PATH
            logger.info("Finished loading QA Reader")
        except OSError:
            logger.error(f"Could not load Question Answer Model")

    @staticmethod
    def initQE(qexp_model_path=QEXP_MODEL_NAME.value):
        """initQE - loads QE model on start
        Args:
        Returns:
        """
        logger.info(f"Loading Pretrained Vector from {qexp_model_path}")
        try:
            ModelLoader.__query_expander = qe.QE(
                qexp_model_path, **QexpConfig.INIT_ARGS
            )
            logger.info("** Loaded Query Expansion Model")
        except Exception as e:
            logger.warning("** Could not load QE model")
            logger.warning(e)

    @staticmethod
    def initQEJBook(qexp_jbook_model_path=QEXP_JBOOK_MODEL_NAME.value):
        """initQE - loads JBOOK QE model on start
        Args:
        Returns:
        """
        logger.info(f"Loading Pretrained Vector from {qexp_jbook_model_path}")
        try:
            ModelLoader.__query_expander_jbook = qe.QE(
                qexp_jbook_model_path, **QexpConfig.INIT_ARGS
            )
            logger.info("** Loaded JBOOK Query Expansion Model")
        except Exception as e:
            logger.warning("** Could not load JBOOK QE model")
            logger.warning(e)

    @staticmethod
    def initWordSim(model_path=WORD_SIM_MODEL.value):
        """initQE - loads QE model on start
        Args:
        Returns:
        """
        logger.info(f"Loading Word Sim Model from {model_path}")
        try:
            ModelLoader.__word_sim = WordSim(model_path)
            logger.info("** Loaded Word Sim Model")
        except Exception as e:
            logger.warning("** Could not load Word Sim model")
            logger.warning(e)

    @staticmethod
    def initSentenceSearcher(
        index_path=SENT_INDEX_PATH.value, transformer_path=LOCAL_TRANSFORMERS_DIR.value
    ):
        """
        initSentenceSearcher - loads SentenceSearcher class on start
        Args:
        Returns:
        """
        logger.info(
            f"Loading Sentence Searcher with sent index path: {index_path}")
        try:

            ModelLoader.__sentence_searcher = SentenceSearcher(
                sim_model_name=SimilarityConfig.BASE_MODEL,
                index_path=index_path,
                transformer_path=transformer_path,
            )

            sim_model = ModelLoader.__sentence_searcher.similarity
            # set cache variable defined in settings.py
            latest_intel_model_sim.value = sim_model.sim_model
            logger.info(
                f"** Loaded Similarity Model from {sim_model.sim_model} and sent index from {index_path}"
            )

        except Exception as e:
            logger.warning("** Could not load Similarity model")
            logger.warning(e)

    @staticmethod
    def initSentenceEncoder(transformer_path=LOCAL_TRANSFORMERS_DIR.value):
        """
        initSentenceEncoder - loads Sentence Encoder on start
        Args:
        Returns:
        """
        logger.info(f"Loading encoder model")
        try:
            ModelLoader.__sentence_encoder = SentenceEncoder(
                encoder_model_name=EmbedderConfig.BASE_MODEL,
                transformer_path=transformer_path,
                processmanager=processmanager,
                **EmbedderConfig.MODEL_ARGS,
            )
            encoder_model = ModelLoader.__sentence_encoder.encoder_model
            # set cache variable defined in settings.py
            latest_intel_model_encoder.value = encoder_model
            logger.info(f"** Loaded Encoder Model from {encoder_model}")

        except Exception as e:
            logger.warning("** Could not load Encoder model")
            logger.warning(e)

    @staticmethod
    def initDocumentCompareSearcher(
        index_path=DOC_COMPARE_SENT_INDEX_PATH.value,
        transformer_path=LOCAL_TRANSFORMERS_DIR.value,
    ):
        """
        initDocumentCompareSearcher - loads SentenceSearcher class on start
        Args:
        Returns:
        """
        logger.info(
            f"Loading Document Compare Searcher with index path: {index_path}")
        try:
            ModelLoader.__document_compare_searcher = DocCompareSentenceSearcher(
                sim_model_name=DocCompareSimilarityConfig.BASE_MODEL,
                index_path=index_path,
                transformer_path=transformer_path,
            )
            sim_model = ModelLoader.__document_compare_searcher.similarity
            # set cache variable defined in settings.py
            latest_doc_compare_sim.value = sim_model.sim_model
            logger.info(
                f"** Loaded Doc Compare Similarity model from {sim_model.sim_model} and sent index from {index_path}"
            )

        except Exception as e:
            logger.warning("** Could not load Doc Compare Similarity model")
            logger.warning(e)

    @staticmethod
    def initDocumentCompareEncoder(transformer_path=LOCAL_TRANSFORMERS_DIR.value):
        """
        initDocumentCompareEncoder - loads Document Compare Encoder on start
        Args:
        Returns:
        """
        logger.info(f"Loading document compare encoder model")
        try:
            ModelLoader.__document_compare_encoder = DocCompareSentenceEncoder(
                encoder_model_name=DocCompareEmbedderConfig.BASE_MODEL,
                transformer_path=transformer_path,
                processmanager=processmanager,
                **DocCompareEmbedderConfig.MODEL_ARGS,
            )
            encoder_model = ModelLoader.__document_compare_encoder.encoder_model
            # set cache variable defined in settings.py
            latest_doc_compare_encoder.value = encoder_model
            logger.info(
                f"** Loaded Doc Compare Encoder Model from {encoder_model}")

        except Exception as e:
            logger.warning("** Could not load Doc Compare Encoder model")
            logger.warning(e)

    @staticmethod
    def initSparse(model_name=latest_intel_model_trans.value):
        try:
            ModelLoader.__sparse_reader = sparse.SparseReader(
                model_name=model_name)
            logger.info(f"Sparse Reader: {model_name} loaded")
        except Exception as e:
            logger.warning("** Could not load Sparse Reader")
            logger.warning(e)

    @staticmethod
    def initTopics(model_path=TOPICS_MODEL.value) -> None:
        """initTopics - load topics model on start
        Args:
        Returns:
        """
        try:
            logger.info(f"Loading topic model {model_path}")
            logger.info(TopicsConfig.DATA_ARGS)
            ModelLoader.__topic_model = Topics(directory=model_path)
            logger.info("Finished loading Topic Model")
        except Exception as e:
            logger.warning("** Could not load Topic model")
            logger.warning(e)

    @staticmethod
    def initRecommender():
        """initRecommender - loads recommender class on start
        Args:
        Returns:
        """
        try:
            logger.info("Starting Recommender pipeline")
            ModelLoader.__recommender = Recommender()
            logger.info("Finished loading Recommender")
        except OSError:
            logger.error(f"** Could not load Recommender")
