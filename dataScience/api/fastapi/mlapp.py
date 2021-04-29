from fastapi import FastAPI, Query, Body, Response, status
from fastapi_utils.tasks import repeat_every
import sys
import subprocess

# must import sklearn first or you get an import error
import sklearn
import spacy
from dataScience.src.search.embed_reader import sparse
from dataScience.src.search.query_expansion import qe
from dataScience.src.search.sent_transformer.model import SentenceSearcher
from dataScience.src.utilities import transformerUtil as t_util
from dataScience.src.utilities import utils
from dataScience.src.search.QA.QAReader import DocumentReader as QAReader
from dataScience.api.fastapi.model_config import Config
from dataScience.api.utils.pathselect import get_model_paths
from dataScience.src.search.query_expansion.utils import remove_original_kw
from dataScience.src.featurization.keywords.extract_keywords import get_keywords

# from dataScience.models.topic_models.tfidf import bigrams, tfidf_model
from dataScience.src.text_handling.process import topic_processing
from dataScience.src.featurization.summary import GensimSumm

import urllib3
import redis
import faulthandler
from pydantic import BaseModel, Json
import requests
import os
import json
import logging
import en_core_web_lg

# start API
app = FastAPI()
# set loggers
logger = logging.getLogger()
glogger = logging.getLogger("gunicorn.error")
logger.setLevel(logging.DEBUG)

log_formatter = logging.Formatter(
    "%(asctime)s [%(levelname)s][PID:%(process)d]: %(message)s"
)
ch = logging.StreamHandler(sys.stdout)
ch.setFormatter(log_formatter)
logger.addHandler(ch)
glogger.addHandler(ch)
log_file_path = "dataScience/api/logs/gc_ml_logs.txt"
fh = logging.handlers.RotatingFileHandler(
    log_file_path, maxBytes=2000000, backupCount=1, mode="a"
)
logger.info(f"ML API is logging to {log_file_path}")

fh.setFormatter(log_formatter)
logger.addHandler(fh)
glogger.addHandler(fh)
# app.add_middleware = (CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# get environ vars
GC_ML_HOST = os.environ.get("GC_ML_HOST", default="localhost")
REDIS_HOST = os.environ.get("REDIS_HOST", default="localhost")
REDIS_PORT = os.environ.get("REDIS_PORT", default="6379")
if REDIS_HOST == "":
    REDIS_HOST = "localhost"
if REDIS_PORT == "":
    REDIS_PORT = 6379
if GC_ML_HOST == "":
    GC_ML_HOST = "localhost"
ignore_files = ["._.DS_Store", ".DS_Store", "index"]

model_path_dict = get_model_paths()
LOCAL_TRANSFORMERS_DIR = model_path_dict["transformers"]
SENT_INDEX_PATH = model_path_dict["sentence"]
QEXP_MODEL_NAME = model_path_dict["qexp"]
t_list = []
try:
    t_list = [trans for trans in os.listdir(
        LOCAL_TRANSFORMERS_DIR) if "." not in trans]
except Exception as e:
    logger.warning("No transformers folder")
    logger.warning(e)
logger.info(f"API AVAILABLE TRANSFORMERS are: {t_list}")

# redis init
try:
    cache = redis.Redis(REDIS_HOST, port=int(REDIS_PORT))
except Exception as e:
    logger.error(
        " *** Unable to connect to redis {REDIS_HOST} {REDIS_PORT}***")
    logger.error(e)

# validate correct configurations
logger.info(f"API TRANSFORMERS DIRECTORY is: {LOCAL_TRANSFORMERS_DIR}")
logger.info(f"API INDEX PATH is: {SENT_INDEX_PATH}")
logger.info(f"API REDIS HOST is: {REDIS_HOST}")
logger.info(f"API REDIS PORT is: {REDIS_PORT}")


# init globals
query_expander = None
sparse_reader = None
latest_intel_model = None
sentence_trans = None
latest_sentence_models = None
qa_model = None

faulthandler.enable()


def check_dep_exist():
    healthy = True
    if not os.path.isdir(LOCAL_TRANSFORMERS_DIR):
        logger.warning(f"{LOCAL_TRANSFORMERS_DIR} does NOT exist")
        healthy = False

    if not os.path.isdir(SENT_INDEX_PATH):
        logger.warning(f"{SENT_INDEX_PATH} does NOT exist")
        healthy = False

    if not os.path.isdir(QEXP_MODEL_NAME):
        logger.warning(f"{QEXP_MODEL_NAME} does NOT exist")
        healthy = False
    # topics_dir = os.path.join(QEXP_MODEL_NAME, "topic_models/models")
    # if not os.path.isdir(topics_dir):
    #    logger.warning(f"{topics_dir} does NOT exist")
    #    healthy = False

    return healthy


@app.on_event("startup")
async def initQA():
    """initQA - loads transformer model on start
    Args:
    Returns:
    """
    try:
        global qa_model
        qa_model_path = os.path.join(
            LOCAL_TRANSFORMERS_DIR, "bert-base-cased-squad2")
        logger.info("Starting QA pipeline")
        qa_model = QAReader(qa_model_path)
        cache.set("latest_qa_model", qa_model_path)
        logger.info("Finished loading QA Reader")
    except OSError:
        logger.error(f"Could not load Question Answer Model")


@app.on_event("startup")
async def initQE(qexp_model_path=QEXP_MODEL_NAME):
    """initQE - loads QE model on start
    Args:
    Returns:
    """
    logger.info(f"Loading Query Expansion Model from {QEXP_MODEL_NAME}")
    global query_expander
    try:
        query_expander = qe.QE(
            qexp_model_path, method="emb", vocab_file="word-freq-corpus-20201101.txt"
        )
        logger.info("** Loaded Query Expansion Model")
    except Exception as e:
        logger.warning("** Could not load QE model")
        logger.warning(e)


# Currently deprecated


@app.on_event("startup")
async def initTrans():
    """initTrans - loads transformer model on start
    Args:
    Returns:
    """
    try:
        global sparse_reader
        global latest_intel_model
        model_name = os.path.join(
            LOCAL_TRANSFORMERS_DIR, "distilbert-base-uncased-distilled-squad"
        )
        # not loading due to ram and deprecation
        # logger.info(f"Attempting to load in BERT model default: {model_name}")
        logger.info(
            f"SKIPPING LOADING OF TRANSFORMER MODEL FOR INTELLIGENT SEARCH: {model_name}"
        )
        # sparse_reader = sparse.SparseReader(model_name=model_name)
        latest_intel_model = model_name
        # logger.info(
        #    f" ** Successfully loaded BERT model default: {model_name}")
        logger.info(f" ** Setting Redis model to {model_name}")
        cache.set("latest_intel_model_trans", latest_intel_model)
    except OSError:
        logger.error(f"Could not load BERT Model {model_name}")
        logger.error(
            "Check if BERT cache is in correct location: tranformer_cache/ above root directory."
        )


@app.on_event("startup")
async def initSentence(
    index_path=SENT_INDEX_PATH, transformer_path=LOCAL_TRANSFORMERS_DIR
):
    """
    initQE - loads Sentence Transformers on start
    Args:
    Returns:
    """
    global sentence_trans
    # load defaults
    encoder_model = os.path.join(
        transformer_path, "msmarco-distilbert-base-v2")
    logger.info(f"Using {encoder_model} for sentence transformer")
    sim_model = os.path.join(transformer_path, "distilbart-mnli-12-3")
    logger.info(f"Loading Sentence Transformer from {sim_model}")
    logger.info(f"Loading Sentence Index from {index_path}")
    try:
        sentence_trans = SentenceSearcher(
            index_path=index_path,
            sim_model=sim_model,
        )

        cache.hmset(
            "latest_intel_model_sent", {
                "encoder": encoder_model, "sim": sim_model}
        )
        logger.info("** Loaded Sentence Transformers")
    except Exception as e:
        logger.warning("** Could not load Sentence Transformer model")
        logger.warning(e)


@app.on_event("startup")
@repeat_every(seconds=120, wait_first=True)
async def check_health():
    """check_health - periodically checks redis for a new model for workers, checks access to end points
    Args:
    Returns:
    """
    logger.info("API Health Check")
    try:
        new_trans_model_name = str(
            cache.get("latest_intel_model_trans").decode("utf-8")
        )
        new_sent_model_name = str(cache.hgetall("latest_intel_model_sent"))
        new_qa_model_name = str(cache.get("latest_qa_model").decode("utf-8"))
    except Exception as e:
        logger.info("Could not get one of the model names from redis")
        logger.info(e)
    try:
        global sparse_reader
        good_health = True
        if (sparse_reader is not None) and (
            sparse_reader.model_name != new_trans_model_name
        ):
            logger.info(
                f"Process does not have {new_trans_model_name} loaded - has {sparse_reader.model_name}"
            )
            sparse_reader = sparse.SparseReader(
                model_name=new_trans_model_name)
            logger.info(f"{new_trans_model_name} loaded")
            good_health = False
    except Exception as e:
        logger.info("Model Health: POOR")
        logger.warn(
            f"Model Health: BAD - Error with reloading model {new_trans_model_name}"
        )
    if check_dep_exist:
        good_health = True
    else:
        good_health = False
    if good_health:
        logger.info("Model Health: GOOD")
    else:
        logger.info("Model Health: POOR")

    # logger.info(f"-- Transformer model name: {new_trans_model_name}")
    logger.info(f"-- Sentence Transformer model name: {new_sent_model_name}")
    logger.info(f"-- QE model name: {QEXP_MODEL_NAME}")
    logger.info(f"-- QA model name: {new_qa_model_name}")


@app.get("/")
async def home():
    return {"API": "FOR TRANSFORMERS"}


@app.post("/transformerSearch", status_code=200)
async def transformer_infer(query: dict, response: Response) -> dict:
    """transformer_infer - endpoint for transformer inference
    Args:
        query: dict; format of query
            {"query": "test", "documents": [{"text": "...", "id": "xxx"}, ...]
        Response: Response class; for status codes(apart of fastapi do not need to pass param)
    Returns:
        results: dict; results of inference
    """
    logger.debug("TRANSFORMER - predicting query: " + str(query))
    results = {}
    try:
        results = sparse_reader.predict(query)
        logger.info(results)
    except Exception:
        logger.error(f"Unable to get results from transformer for {query}")
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        raise
    return results


@app.post("/textExtractions", status_code=200)
async def textExtract_infer(query: dict, extractType: str, response: Response) -> dict:
    """textExtract_infer - endpoint for sentence transformer inference
    Args:
        query: dict; format of query
            {"text": "i am text"}
        Response: Response class; for status codes(apart of fastapi do not need to pass param)
        extractType: topics, keywords, or summary
    Returns:
        results: dict; results of inference
    """
    results = {}
    try:
        query_text = query["text"]
        results["extractType"] = extractType
        if extractType == "topics":
            logger.debug("TOPICS - predicting query: " + str(query))
            # topics = tfidf_model.get_topics(
            #    topic_processing(query_text, bigrams), topn=5
            # )
            # logger.info(topics)
            # results["extracted"] = topics
        elif extractType == "summary":
            summary = GensimSumm(
                query_text, long_doc=False, word_count=30
            ).make_summary()
            results["extracted"] = summary
        elif extractType == "keywords":
            logger.debug("keywords - predicting query: " + str(query))
            results["extracted"] = get_keywords(query_text)

    except Exception:
        logger.error(f"Unable to get extract text for {query}")
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        raise
    return results


@app.post("/transSentenceSearch", status_code=200)
async def trans_sentence_infer(
    query: dict, response: Response, num_results: int = 5
) -> dict:
    """trans_sentence_infer - endpoint for sentence transformer inference
    Args:
        query: dict; format of query
            {"text": "i am text"}
        Response: Response class; for status codes(apart of fastapi do not need to pass param)
    Returns:
        results: dict; results of inference
    """
    logger.debug("SENTENCE TRANSFORMER - predicting query: " + str(query))
    results = {}
    try:
        query_text = query["text"]
        results = sentence_trans.search(query_text, n_returns=num_results)
        logger.info(results)
    except Exception:
        logger.error(
            f"Unable to get results from sentence transformer for {query}")
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        raise
    return results


@app.post("/questionAnswer", status_code=200)
async def qa_infer(query: dict, response: Response) -> dict:
    """qa_infer - endpoint for sentence transformer inference
    Args:
        query: dict; format of query, text must be concatenated string
            {"query": "what is the navy",
            "search_context":["pargraph 1", "xyz"]}
        Response: Response class; for status codes(apart of fastapi do not need to pass param)
    Returns:
        results: dict; results of inference
    """
    logger.debug("QUESTION ANSWER - predicting query: " + str(query["query"]))
    results = {}
    try:
        query_text = query["query"]
        query_context = query["search_context"]
        context = ""
        # need 10 documents
        for page in query_context:
            context = "\n\n".join([context, page])

        answers = qa_model.wiki_answer(query_text, context)
        answers_list = answers.split("/")
        answers_list = [x.strip() for x in answers_list if x.rstrip()]
        logger.info(answers_list)
        results["answers"] = answers_list

        results["question"] = query_text
    except Exception:
        logger.error(f"Unable to get results from QA model for {query}")
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


@app.post("/expandTerms", status_code=200)
async def post_expand_query_terms(termsList: dict, response: Response) -> dict:
    """post_expand_query_terms - endpoint for expand query terms
    Args:
        termsList: dict;
        Response: Response class; for status codes(apart of fastapi do not need to pass param)
    Returns:
        expansion_dict: dict; expanded dictionary of terms
    """
    termsList = termsList["termsList"]
    expansion_dict = {}
    # logger.info("[{}] expanded: {}".format(user, termsList))

    logger.info(f"Expanding: {termsList}")
    try:
        for term in termsList:
            term = unquoted(term)
            expansion_list = query_expander.expand(term)
            # turn word pairs into search phrases since otherwise it will just search for pages with both words on them
            # removing original word from the return terms unless it is combined with another word
            logger.info(f"original expanded terms: {expansion_list}")
            finalTerms = remove_original_kw(expansion_list, term)
            expansion_dict[term] = ['"{}"'.format(exp) for exp in finalTerms]
            logger.info(f"-- Expanded {term} to \n {finalTerms}")
        return expansion_dict
    except:
        logger.error(f"Error with query expansion on {termsList}")
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR


@app.post("/updateModel", status_code=200)
async def load_latest_models(model_dict: dict, response: Response):
    """load_latest_models - endpoint for updating the transformer model
    Args:
        model_dict: dict; {"model_name": "bert..."}

        Response: Response class; for status codes(apart of fastapi do not need to pass param)
    Returns:
    """
    model_name = model_dict["model_name"]
    try:
        # sparse_reader.load(model_name)
        global sparse_reader
        logger.info(
            "Attempting to create new sparse reader object with model {}".format(
                model_name
            )
        )
        model_name = os.path.join(LOCAL_TRANSFORMERS_DIR, model_name)
        sparse_reader = sparse.SparseReader(model_name=model_name)
        global latest_intel_model
        latest_intel_model = model_name
        cache.set("latest_intel_model_trans", latest_intel_model)
        logger.info(f"Loaded {model_name}")

        return {"model_name": model_name}

    except Exception as e:
        logger.error("Load latest model error {}".format(e))
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"error": "Load latest model failed: 404"}


@app.get("/getTransformerList")
async def get_trans_list():
    """get_trans_list - gets available transformers from model dir
    Args:
    Returns:
        t_list: list; of transformers
    """
    try:
        logger.info("Reading transformer list")
        t_list = [
            trans
            for trans in os.listdir(LOCAL_TRANSFORMERS_DIR)
            if trans not in ignore_files
        ]

        return t_list
    except:
        logger.error(f"Could not read {LOCAL_TRANSFORMERS_DIR}")
        return []


@app.get("/getCurrentTransformer")
async def get_trans_model():
    """get_trans_model - endpoint for current transformer
    Args:
    Returns:
        dict of model name
    """
    # deprecated
    # intel_model = cache.get("latest_intel_model_trans").decode("utf-8")
    sent_model = cache.hgetall("latest_intel_model_sent")
    return {
        "sentence_models": sent_model,
        # "model_name": intel_model,
    }


@app.get("/reloadModels", status_code=200)
async def reload_models(response: Response):
    model_path_dict = get_model_paths()
    logger.info("Attempting to load QE")
    await initQE(model_path_dict["qexp"])
    logger.info("Attempting to load QA")
    await initQA()
    logger.info("Attempting to load Sentence Transformer")
    await initSentence(
        index_path=model_path_dict["sentence"],
        transformer_path=model_path_dict["transformers"],
    )

    logger.info("Reload Complete")
    return


@app.get("/download", status_code=200)
async def download(response: Response):
    """download - downloads dependencies from s3
    Args:
        model: str
    Returns:
    """
    try:
        logger.info("Attempting to download dependencies from S3")
        output = subprocess.call(
            ["dataScience/scripts/download_dependencies.sh"])
        # get_transformers(overwrite=False)
        # get_sentence_index(overwrite=False)
    except:
        logger.warning(f"Could not get dependencies from S3")
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    return


@app.get("/s3", status_code=200)
async def s3_func(function, response: Response):
    """s3_func - s3 functionality for model managment
    Args:
        model: str
    Returns:
    """
    try:
        logger.info("Attempting to download dependencies from S3")
        s3_path = "gamechanger/models/"
        if function == "models":
            models = utils.get_models_list(s3_path)
    except:
        logger.warning(f"Could not get dependencies from S3")
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    return models
