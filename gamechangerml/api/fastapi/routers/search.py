from fastapi import APIRouter, Response, status
import time
import requests
import base64
import hashlib
import datetime

# must import sklearn first or you get an import error
from gamechangerml.src.search.query_expansion.utils import remove_original_kw
from gamechangerml.src.featurization.keywords.extract_keywords import get_keywords
from gamechangerml.src.text_handling.process import preprocess
from gamechangerml.api.fastapi.version import __version__
from gamechangerml.src.utilities import gc_web_api
from gamechangerml.api.utils.redisdriver import CacheVariable

# from gamechangerml.models.topic_models.tfidf import bigrams, tfidf_model
# from gamechangerml.src.featurization.summary import GensimSumm
from gamechangerml.api.fastapi.settings import CACHE_EXPIRE_DAYS
from gamechangerml.api.utils.logger import logger
from gamechangerml.api.fastapi.model_loader import ModelLoader

from gamechangerml.configs import QexpConfig

router = APIRouter()
MODELS = ModelLoader()


@router.post("/transformerSearch", status_code=200)
async def transformer_infer(body: dict, response: Response) -> dict:
    """transformer_infer - endpoint for transformer inference
    Args:
        body: dict; json format of query
            {"query": "test", "documents": [{"text": "...", "id": "xxx"}, ...]
        Response: Response class; for status codes(apart of fastapi do not need to pass param)
    Returns:
        results: dict; results of inference
    """
    logger.debug("TRANSFORMER - predicting query: " + str(body))
    results = {}
    try:
        results = MODELS.sparse_reader.predict(body)
        logger.info(results)
    except Exception:
        logger.error(f"Unable to get results from transformer for {body}")
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        raise
    return results


@router.post("/textExtractions", status_code=200)
async def textExtract_infer(body: dict, extractType: str, response: Response) -> dict:
    """textExtract_infer - endpoint for sentence transformer inference
    Args:
        body: dict; json format of query
            {"text": "i am text"}
        Response: Response class; for status codes(apart of fastapi do not need to pass param)
        extractType: url query string; one of topics, keywords, or summary
    Returns:
        results: dict; results of inference
    """
    results = {}
    try:
        query_text = body["text"]
        results["extractType"] = extractType
        if extractType == "topics":
            logger.debug("TOPICS - predicting query: " + str(body))
            topics = MODELS.topic_model.get_topics_from_text(query_text)
            logger.info(topics)
            results["extracted"] = topics
        elif extractType == "summary":
            # gensim upgrade breaks GensimSumm class
            # summary = GensimSumm(
            #     query_text, long_doc=False, word_count=30
            # ).make_summary()
            # results["extracted"] = summary
            results["extracted"] = "Summary is not supported at this time"
        elif extractType == "keywords":
            logger.debug("keywords - predicting query: " + str(body))
            results["extracted"] = get_keywords(query_text)

    except Exception:
        logger.error(f"Unable to get extract text for {body}")
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        raise
    return results


@router.post("/transSentenceSearch", status_code=200)
async def trans_sentence_infer(
    body: dict,
    response: Response,
    num_results: int = 10,
    process: bool = True,
    externalSim: bool = False,
    threshold="auto",
) -> dict:
    """trans_sentence_infer - endpoint for sentence transformer inference
    Args:
        body: dict; json format of query
            {"text": "i am text"}
        Response: Response class; for status codes(apart of fastapi do not need to pass param)
    Returns:
        results: dict; results of inference
    """
    logger.debug("SENTENCE TRANSFORMER - predicting query: " + str(body))
    results = {}
    try:
        query_text = body["text"]
        cache = CacheVariable(query_text, True)
        cached_value = cache.get_value()
        if cached_value:
            logger.info("Searched was found in cache")
            results = cached_value
        else:
            results = MODELS.sentence_searcher.search(
                query_text,
                num_results,
                process=process,
                externalSim=False,
                threshold=threshold,
            )
            cache.set_value(
                results,
                expire=int(
                    (
                        datetime.datetime.utcnow()
                        + datetime.timedelta(days=CACHE_EXPIRE_DAYS)
                    ).timestamp()
                ),
            )
        logger.info(results)
    except Exception:
        logger.error(
            f"Unable to get results from sentence transformer for {body}")
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        raise
    return results


@router.post("/questionAnswer", status_code=200)
async def qa_infer(body: dict, response: Response) -> dict:
    """qa_infer - endpoint for sentence transformer inference
    Args:
        body: dict; json format of query, text must be concatenated string
            {"query": "what is the navy",
            "search_context":["pargraph 1", "xyz"]}
        Response: Response class; for status codes(apart of fastapi do not need to pass param)
    Returns:
        results: dict; results of inference
    """
    logger.debug("QUESTION ANSWER - predicting query: " + str(body["query"]))
    results = {}

    try:
        query_text = body["query"]
        query_context = body["search_context"]
        start = time.perf_counter()
        answers = MODELS.qa_model.answer(query_text, query_context)
        end = time.perf_counter()
        logger.info(answers)
        logger.info(f"time: {end - start:0.4f} seconds")
        results["answers"] = answers
        results["question"] = query_text

    except Exception:
        logger.error(f"Unable to get results from QA model for {body}")
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        raise
    return results


@router.post("/expandTerms", status_code=200)
async def post_expand_query_terms(body: dict, response: Response) -> dict:
    """post_expand_query_terms - endpoint for expand query terms
    Args:
        body: dict; json format of query
        Response: Response class; for status codes(apart of fastapi do not need to pass param)
    Returns:
        expansion_dict: dict; expanded dictionary of terms
    """

    terms_string = " ".join(body["termsList"])
    terms = preprocess(terms_string, remove_stopwords=True)
    expansion_dict = {}
    # logger.info("[{}] expanded: {}".format(user, termsList))

    logger.info(f"Expanding: {body}")
    query_expander = (
        MODELS.query_expander
        if body.get("qe_model", "gc_core") != "jbook"
        or MODELS.query_expander_jbook is None
        else MODELS.query_expander_jbook
    )
    try:
        terms_string = unquoted(terms_string)
        expansion_list = query_expander.expand(
            terms_string, **QexpConfig.EXPANSION_ARGS
        )
        # Pass entire query from frontend to query expansion model and return topn.
        # Removes original word from the return terms unless it is combined with another word
        logger.info(f"original expanded terms: {expansion_list}")
        finalTerms = remove_original_kw(expansion_list, terms_string)
        expansion_dict[terms_string] = [
            '"{}"'.format(exp) for exp in finalTerms]
        logger.info(f"-- Expanded {terms_string} to \n {finalTerms}")
        # Perform word similarity
        logger.info(f"Finding similiar words for: {terms_string}")
        sim_words_dict = MODELS.word_sim.most_similiar_tokens(terms_string)
        logger.info(f"-- Expanded {terms_string} to \n {sim_words_dict}")
        # Construct return payload
        expanded_words = {}
        expanded_words["qexp"] = expansion_dict
        expanded_words["wordsim"] = sim_words_dict
        return expanded_words
    except Exception as e:
        logger.error(f"Error with query expansion on {body}")
        logger.error(e)
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR


@router.post("/wordSimilarity", status_code=200)
async def post_word_sim(body: dict, response: Response) -> dict:
    """post_word_sim - endpoint for getting similar words
    Args:
        body: dict; json format of query
        Response: Response class; for status codes(apart of fastapi do not need to pass param)
    Returns:
        expansion_dict: dict; expanded dictionary of terms
    """
    # logger.info("[{}] expanded: {}".format(user, termsList))
    terms = body["text"]
    logger.info(f"Finding similiar words for: {terms}")
    try:
        sim_words_dict = MODELS.word_sim.most_similiar_tokens(terms)
        logger.info(f"-- Expanded {terms} to \n {sim_words_dict}")
        return sim_words_dict
    except:
        logger.error(f"Error with query expansion on {terms}")
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR


@router.post("/recommender", status_code=200)
async def post_recommender(body: dict, response: Response) -> dict:
    results = {}
    sample = False
    try:
        filenames = body["filenames"]
        if not filenames:
            if body["sample"]:
                sample = body["sample"]
        logger.info(f"Recommending similar documents to {filenames}")
        results = MODELS.recommender.get_recs(
            filenames=filenames, sample=sample)
        if results["results"] != []:
            logger.info(f"Found similar docs: \n {str(results)}")
        else:
            logger.info("Did not find any similar docs")
    except Exception as e:
        logger.warning(f"Could not get similar docs for {filenames}")
        logger.warning(e)
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    return results


@router.post("/documentCompare", status_code=200)
async def document_compare_infer(
    body: dict,
    response: Response,
    num_results: int = 10,
    process: bool = True,
) -> dict:
    """document_compare_infer - endpoint for document compare inference
    Args:
        body: dict; json format of query
            {
                <str> "text": "i am text",
                <?array[[threshold, display]] "confidences": optional array of 2 tuples (threshold, display) where score > threshold -> display :: default [[0.8, "High"], [0.5, "Medium"], [0.4, "Low"]]
                <?float> "cutoff": optional cutoff to filter result scores by
            }
        Response: Response class; for status codes(apart of fastapi do not need to pass param)
    Returns:
        results: dict; results of inference
    """
    logger.debug("DOCUMENT COMPARE INFER - predicting query: " + str(body))
    results = {}
    try:
        query_text = body["text"]
        results = MODELS.document_compare_searcher.search(
            query_text, num_results, body, process=process, externalSim=False
        )
        logger.info(results)
    except Exception:
        logger.error(
            f"Unable to get results from doc compare sentence transformer for {body}"
        )
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        raise
    return results


def unquoted(term):
    """unquoted - unquotes string
    Args:
        term: string
    Returns:
        term: without quotes
    """
    if term[0] in ["'", '"'] and term[-1] in ["'", '"']:
        return term[1:-1]
    else:
        return term
