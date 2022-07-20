from fastapi import APIRouter
from fastapi_utils.tasks import repeat_every
import os
from gamechangerml.api.fastapi.settings import (
    DOC_COMPARE_SENT_INDEX_PATH,
    logger,
    TOPICS_MODEL,
    MODEL_LOAD_FLAG,
    QEXP_JBOOK_MODEL_NAME,
    QEXP_MODEL_NAME,
    LOCAL_TRANSFORMERS_DIR,
    SENT_INDEX_PATH,
    latest_intel_model_encoder,
    latest_intel_model_sim,
    latest_intel_model_sent,
    latest_doc_compare_sim,
    latest_doc_compare_encoder,
)
from gamechangerml.api.fastapi.model_loader import ModelLoader

router = APIRouter()
MODELS = ModelLoader()


@router.on_event("startup")
async def load_models():
    if MODEL_LOAD_FLAG:
        MODELS.initQA()
        MODELS.initQE()
        MODELS.initQEJBook()
        MODELS.initSentenceEncoder()
        MODELS.initSentenceSearcher()
        MODELS.initWordSim()
        MODELS.initTopics()
        MODELS.initRecommender()
        MODELS.initDocumentCompareEncoder()
        MODELS.initDocumentCompareSearcher()
        logger.info("AFTER LOAD MODELS")
    else:
        logger.info("MODEL_LOAD_FLAG set to False, no models loaded")


@router.on_event("startup")
@repeat_every(seconds=120, wait_first=True)
async def check_health():
    """check_health - periodically checks redis for a new model for workers, checks access to end points
    Args:
    Returns:
    """
    logger.info("API Health Check")
    try:
        new_sim_model_name = str(latest_intel_model_sim.value)
        new_encoder_model_name = str(latest_intel_model_encoder.value)
        new_sent_model_name = str(latest_intel_model_sent.value)
    except Exception as e:
        logger.info("Could not get one of the model names from redis")
        logger.info(e)
    if check_dep_exist:
        good_health = True
    else:
        good_health = False
    if good_health:
        logger.info("Model Health: GOOD")
    else:
        logger.info("Model Health: POOR")

    # logger.info(f"-- Transformer model name: {new_trans_model_name}")
    # logger.info(f"-- Sentence Transformer model name: {new_sent_model_name}")
    logger.info(f"-- Sentence Similarity model name: {new_sim_model_name}")
    logger.info(f"-- Sentence Encoder model name: {new_encoder_model_name}")
    logger.info(f"-- Sentence index name: {SENT_INDEX_PATH.value}")
    logger.info(f"-- QE model name: {QEXP_MODEL_NAME.value}")
    logger.info(f"-- QE JBOOK model name: {QEXP_JBOOK_MODEL_NAME.value}")
    logger.info(f"-- Topics model name: {TOPICS_MODEL.value}")
    logger.info(
        f"-- Doc Compare Similarity model name: {latest_doc_compare_sim.value}")
    logger.info(
        f"-- Doc Compare Encoder model name: {latest_doc_compare_encoder.value}"
    )
    logger.info(
        f"-- Doc Compare Sentence index name: {DOC_COMPARE_SENT_INDEX_PATH.value}"
    )


def check_dep_exist():
    healthy = True
    if not os.path.isdir(LOCAL_TRANSFORMERS_DIR.value):
        logger.warning(f"{LOCAL_TRANSFORMERS_DIR.value} does NOT exist")
        healthy = False

    if not os.path.isdir(SENT_INDEX_PATH.value):
        logger.warning(f"{SENT_INDEX_PATH.value} does NOT exist")
        healthy = False

    if not os.path.isdir(DOC_COMPARE_SENT_INDEX_PATH.value):
        logger.warning(f"{DOC_COMPARE_SENT_INDEX_PATH.value} does NOT exist")
        healthy = False

    if not os.path.isdir(QEXP_MODEL_NAME.value):
        logger.warning(f"{QEXP_MODEL_NAME.value} does NOT exist")
        healthy = False

    if not os.path.isdir(TOPICS_MODEL.value):
        logger.warning(f"{TOPICS_MODEL.value} does NOT exist")
        healthy = False

    if not os.path.isdir(QEXP_JBOOK_MODEL_NAME.value):
        logger.warning(f"{QEXP_JBOOK_MODEL_NAME.value} does NOT exist")
        healthy = False

    return healthy
