import os
import logging
from dataScience.api.fastapi.model_config import Config

logger = logging.getLogger()


def get_model_paths():
    model_dict = {}
    # QEXP MODEL
    try:
        qexp_names = [
            f
            for f in os.listdir(Config.LOCAL_PACKAGED_MODELS_DIR)
            if ("qexp_" in f) and ("tar" not in f)
        ]
        qexp_names.sort(reverse=True)
        if len(qexp_names) > 0:
            QEXP_MODEL_PATH = os.path.join(
                Config.LOCAL_PACKAGED_MODELS_DIR, qexp_names[0]
            )
        else:
            print("defaulting INDEX_PATH to qexp")
            QEXP_MODEL_PATH = os.path.join(
                Config.LOCAL_PACKAGED_MODELS_DIR, "qexp_20201217"
            )
    except Exception as e:
        logger.error(e)
        logger.info("Cannot get QEXP model path")

    # TRANSFORMER MODEL PATH
    try:
        LOCAL_TRANSFORMERS_DIR = os.path.join(
            Config.LOCAL_PACKAGED_MODELS_DIR, "transformers"
        )
    except Exception as e:
        logger.error(e)

        logger.info("Cannot get TRANSFORMER model path")
    # SENTENCE INDEX
    # get largest file name with sent_index prefix (by date)
    try:
        sent_index_name = [
            f
            for f in os.listdir(Config.LOCAL_PACKAGED_MODELS_DIR)
            if ("sent_index" in f) and ("tar" not in f)
        ]
        sent_index_name.sort(reverse=True)
        if len(sent_index_name) > 0:
            INDEX_PATH = os.path.join(
                Config.LOCAL_PACKAGED_MODELS_DIR, sent_index_name[0]
            )
        else:
            print("defaulting INDEX_PATH to sent_index")
            INDEX_PATH = os.path.join(
                Config.LOCAL_PACKAGED_MODELS_DIR, "sent_index")
    except Exception as e:
        logger.error(e)
        logger.info("Cannot get Sentence Index model path")
    model_dict = {
        "transformers": LOCAL_TRANSFORMERS_DIR,
        "sentence": INDEX_PATH,
        "qexp": QEXP_MODEL_PATH,
    }
    return model_dict
