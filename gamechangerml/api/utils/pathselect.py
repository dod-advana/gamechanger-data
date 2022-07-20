import os
import logging
from gamechangerml.api.fastapi.model_config import Config

logger = logging.getLogger()


def get_model_paths():
    model_dict = {}
    # QEXP MODEL
    try:
        qexp_names = [
            f
            for f in os.listdir(Config.LOCAL_PACKAGED_MODELS_DIR)
            if ("qexp_" in f) and (all(substr not in f for substr in ["tar", "jbook"]))
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
        QEXP_MODEL_PATH = "gamechangerml/models/"

    # QEXP JBOOK MODEL
    try:
        qexp_jbook_names = [
            f
            for f in os.listdir(Config.LOCAL_PACKAGED_MODELS_DIR)
            if (all(substr in f for substr in ["qexp_", "jbook"])) and ("tar" not in f)
        ]
        qexp_jbook_names.sort(reverse=True)
        if len(qexp_jbook_names) > 0:
            QEXP_JBOOK_MODEL_PATH = os.path.join(
                Config.LOCAL_PACKAGED_MODELS_DIR, qexp_jbook_names[0]
            )
        else:
            print("defaulting INDEX_PATH to qexp")
            QEXP_JBOOK_MODEL_PATH = os.path.join(
                Config.LOCAL_PACKAGED_MODELS_DIR, "jbook_qexp_20220131"
            )
    except Exception as e:
        logger.error(e)
        logger.info("Cannot get QEXP JBOOK model path")
        QEXP_JBOOK_MODEL_PATH = "gamechangerml/models/"

    # TRANSFORMER MODEL PATH
    try:
        LOCAL_TRANSFORMERS_DIR = os.path.join(
            Config.LOCAL_PACKAGED_MODELS_DIR, "transformers"
        )
    except Exception as e:
        logger.error(e)

        logger.info("Cannot get TRANSFORMER model path")
    # WORK SIM MODEL PATH
    try:
        WORD_SIM_MODEL_PATH = os.path.join(
            LOCAL_TRANSFORMERS_DIR, "wiki-news-300d-1M.bin"
        )
    except Exception as e:
        logger.error(e)

        logger.info("Cannot get word sim model path")

    # SENTENCE INDEX AND DOC COMPARE INDEX
    # get largest file name with sent_index prefix (by date)
    try:
        sent_index_name = [
            f
            for f in os.listdir(Config.LOCAL_PACKAGED_MODELS_DIR)
            if ("sent_index" in f) and ("tar" not in f)
        ]
        sent_index_name = [
            f
            for f in sent_index_name
            if os.path.isfile(
                os.path.join(Config.LOCAL_PACKAGED_MODELS_DIR, f, "config")
            )
        ]
        sent_index_name.sort(reverse=True)
        if len(sent_index_name) > 0:
            INDEX_PATH = os.path.join(
                Config.LOCAL_PACKAGED_MODELS_DIR, sent_index_name[0]
            )
            DOC_COMPARE_INDEX_PATH = os.path.join(
                Config.LOCAL_PACKAGED_MODELS_DIR, sent_index_name[0]
            )
        else:
            print("defaulting INDEX_PATH to sent_index")
            INDEX_PATH = os.path.join(
                Config.LOCAL_PACKAGED_MODELS_DIR, "sent_index")
            DOC_COMPARE_INDEX_PATH = os.path.join(
                Config.LOCAL_PACKAGED_MODELS_DIR, "sent_index")
    except Exception as e:
        logger.error(e)
        INDEX_PATH = "gamechangerml/models/"
        DOC_COMPARE_INDEX_PATH = INDEX_PATH
        logger.info(f"Cannot get Sentence Index model path {e}",)

    # TOPICS
    try:

        topic_model_dirs = [
            name
            for name in os.listdir(Config.LOCAL_PACKAGED_MODELS_DIR)
            if "topic_model_" in name
            and os.path.isdir(os.path.join(Config.LOCAL_PACKAGED_MODELS_DIR, name))
        ]
        topic_model_dirs.sort(reverse=True)

        if len(topic_model_dirs) > 0:
            TOPICS_PATH = os.path.join(
                Config.LOCAL_PACKAGED_MODELS_DIR, topic_model_dirs[0]
            )
        else:
            raise ValueError(
                f"No topic_model_<date> folders in {Config.LOCAL_PACKAGED_MODELS_DIR}"
            )

    except Exception as e:
        logger.error(e)
        logger.info("Cannot get Topics model path")
        TOPICS_PATH = "gamechangerml/models/"

    model_dict = {
        "transformers": LOCAL_TRANSFORMERS_DIR,
        "sentence": INDEX_PATH,
        "qexp": QEXP_MODEL_PATH,
        "qexp_jbook": QEXP_JBOOK_MODEL_PATH,
        "word_sim": WORD_SIM_MODEL_PATH,
        "topics": TOPICS_PATH,
        "doc_compare": DOC_COMPARE_INDEX_PATH,
    }
    return model_dict
