import os

from gamechangerml.api.utils.pathselect import get_model_paths
from gamechangerml.api.utils.logger import logger
from gamechangerml.api.utils.redisdriver import CacheVariable, REDIS_HOST, REDIS_PORT
from gamechangerml import CORPUS_PATH
from gamechangerml.configs import QAConfig

# get environ vars
GC_ML_HOST = os.environ.get("GC_ML_HOST", default="localhost")
ML_WEB_TOKEN = os.environ.get("ML_WEB_TOKEN", default="")
MEMORY_LOAD_LIMIT = os.environ.get("MEMORY_LOAD_LIMIT", default=None)
if MEMORY_LOAD_LIMIT:
    MEMORY_LOAD_LIMIT = int(MEMORY_LOAD_LIMIT)
MODEL_LOAD_FLAG = os.environ.get("MODEL_LOAD", default=True)
if MODEL_LOAD_FLAG in ["False", "false", "0"]:
    MODEL_LOAD_FLAG = False
else:
    MODEL_LOAD_FLAG = True
CACHE_EXPIRE_DAYS = 15
if GC_ML_HOST == "":
    GC_ML_HOST = "localhost"
ignore_files = ["._.DS_Store", ".DS_Store", "index"]

CORPUS_DIR = CORPUS_PATH
S3_CORPUS_PATH = os.environ.get("S3_CORPUS_PATH")

# Redis Cache Variables
latest_intel_model_sent = CacheVariable("latest_intel_model_sent", True)
latest_intel_model_sim = CacheVariable(
    "latest sentence searcher (similarity model + sent index)", True
)
latest_intel_model_encoder = CacheVariable("latest encoder model", True)
latest_intel_model_trans = CacheVariable("latest_intel_model_trans")
latest_doc_compare_encoder = CacheVariable(
    "latest doc compare encoder model", True)
latest_doc_compare_sim = CacheVariable(
    "latest doc compare searcher (similarity model + sent index)", True
)

LOCAL_TRANSFORMERS_DIR = CacheVariable("LOCAL_TRANSFORMERS_DIR")
SENT_INDEX_PATH = CacheVariable("SENT_INDEX_PATH")
QEXP_MODEL_NAME = CacheVariable("QEXP_MODEL_NAME")
QEXP_JBOOK_MODEL_NAME = CacheVariable("QEXP_JBOOK_MODEL_NAME")
WORD_SIM_MODEL = CacheVariable("WORD_SIM_MODEL")
TOPICS_MODEL = CacheVariable("TOPICS_MODEL")
QA_MODEL = CacheVariable("QA_MODEL")
DOC_COMPARE_SENT_INDEX_PATH = CacheVariable("DOC_COMPARE_SENT_INDEX_PATH")


model_path_dict = get_model_paths()
LOCAL_TRANSFORMERS_DIR.value = model_path_dict["transformers"]
SENT_INDEX_PATH.value = model_path_dict["sentence"]
QEXP_MODEL_NAME.value = model_path_dict["qexp"]
QEXP_JBOOK_MODEL_NAME.value = model_path_dict["qexp_jbook"]
WORD_SIM_MODEL.value = model_path_dict["word_sim"]
TOPICS_MODEL.value = model_path_dict["topics"]
QA_MODEL.value = QAConfig.BASE_MODEL
DOC_COMPARE_SENT_INDEX_PATH.value = model_path_dict["doc_compare"]

t_list = []
try:
    t_list = [
        trans for trans in os.listdir(LOCAL_TRANSFORMERS_DIR.value) if "." not in trans
    ]
except Exception as e:
    logger.warning("No transformers folder")
    logger.warning(e)
logger.info(f"API AVAILABLE TRANSFORMERS are: {t_list}")


# validate correct configurations
logger.info(f"API TRANSFORMERS DIRECTORY is: {LOCAL_TRANSFORMERS_DIR.value}")
logger.info(f"API INDEX PATH is: {SENT_INDEX_PATH.value}")
logger.info(
    f"API DOC COMPARE INDEX PATH is: {DOC_COMPARE_SENT_INDEX_PATH.value}")
logger.info(f"API REDIS HOST is: {REDIS_HOST}")
logger.info(f"API REDIS PORT is: {REDIS_PORT}")
