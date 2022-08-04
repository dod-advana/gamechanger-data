import heapq as heap
import logging
import warnings

from transformers import pipeline

import gamechangerml.src.search.embed_reader.version as v

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
# logging.basicConfig(level=logging.DEBUG)
ch = logging.StreamHandler()
# create formatter
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
# add formatter to ch
ch.setFormatter(formatter)
# add ch to logger
logger.addHandler(ch)
warnings.simplefilter(action="ignore", category=FutureWarning)


class SparseReader(object):
    __version__ = v.__version__

    def __init__(self, model_name=None, context_window_size=150, use_gpu=False):
        """
        Reader class for predicting answers to a given question using the
        Hugging Face `question-answer` pipeline.

        Args:
            model_name (str): name or path of the Hugging Face transformer
                model

            context_window_size (int): number of characters surrounding the
                predicted answer; defaults to `max(30, context_size_window)`

            use_gpu (bool): Defaults to `False` at this time.

        Raises:
            ValueError: if `model_name` is `None`

            NotImplementedError: if `use_gpu` is `True`; this will be changed
                once a GPU test environment is in place

            OSError: if the the identified `model_name` cannot be loaded

            KeyError: if the `dict` provided to the `predict` method is not
                in the expected format

        To Do:
            - Add GPU support
            - Investigate `handle_impossible_answer=True` - how does this work
                and do we need it?
        """

        if model_name is None:
            raise ValueError("model_name cannot be None")

        self.model_name = model_name
        self.use_gpu = use_gpu
        self.context_window_size = max(30, context_window_size)

        if use_gpu:
            raise NotImplementedError("GPU is not supported at this time")

        logger.info("{} {}".format(self.__class__.__name__, self.__version__))
        logger.info("instantiating base reader")
        logger.info("         model_name : {}".format(model_name))
        logger.info("context_window_size : {}".format(context_window_size))
        logger.info("           use__gpu : {}".format(use_gpu))

        try:
            self.hf_nlp = pipeline(
                "question-answering",
                model=model_name,
                tokenizer=None,
                device=-1,
            )
        except OSError as e:
            logger.exception("{}: {}".format(type(e), str(e)), exc_info=True)
            raise e

    @staticmethod
    def _unpack_json(query_results):
        try:
            question = query_results["query"]
            questions = [question] * len(query_results["documents"])
            docs = [d["text"] for d in query_results["documents"]]
            doc_ids = [d["id"] for d in query_results["documents"]]
            return questions, docs, doc_ids
        except KeyError as e:
            logger.exception("{}: {}".format(type(e), str(e)), exc_info=True)
            raise e

    def predict(self, query_results, top_k=None):
        """
        Accepts the dictionary `query_results`, discovers and ranks the `top_k`
        answers. The ranked results are packaged into a `dict` and returned.
        Examples of the `query_results` and return schema can be found in
        `schema_example/` directory.

        Args:
            query_results (dict): The query, text passages from a retrieved set
                of search results, and document IDs as represented in
                `schema_example/query_results.json`.

            top_k (int|None): The number of `answers` returned. Typically, this
                is less than the number of text passages in `query_results`. If
                `None`, all passages are ranked and returned.

        Returns: dict in the format shown in
            `schema_example/query_results.json`

        """

        questions, docs, doc_ids = self._unpack_json(query_results)
        logger.info("n questions: {}".format(len(questions)))
        logger.info("n docs     : {}".format(len(docs)))

        answers = self.hf_nlp(question=questions, context=docs, topk=1)

        h = list()
        for idx, ans in enumerate(answers):
            ctx = self._make_context(ans["start"], ans["end"], docs[idx])
            doc_dict = {
                "answer": ans["answer"],
                "context": ctx,
                "id": doc_ids[idx],
                "text": docs[idx],
            }
            h.append((ans["score"], doc_dict))
        answers = sorted(h, key=lambda tup: tup[0], reverse=True)
        answers = [ans for _, ans in answers]
        logger.info(
            "Length of answers from transformer nlp: {}".format(len(answers)))

        if top_k is None:
            return self._make_json(questions[0], answers)
        elif int(top_k) > 0:
            return self._make_json(questions[0], answers[: int(top_k)])
        else:
            logger.warning("illegal value for top_k; got {}".format(top_k))
            return self._make_json(questions[0], answers)

    @staticmethod
    def _make_json(question, answers):
        dict_out = {"query": question, "answers": answers}
        return dict_out

    def _make_context(self, start, end, doc_text):
        context_start = max(0, start - self.context_window_size)
        context_end = min(len(doc_text), end + self.context_window_size)
        return doc_text[context_start:context_end]
