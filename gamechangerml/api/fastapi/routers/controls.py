from concurrent.futures import thread
from fastapi import APIRouter, Response, status
import subprocess
import os
import json
import tarfile
import shutil
import threading
import pandas as pd

from datetime import datetime
from gamechangerml import DATA_PATH
from gamechangerml.src.utilities import utils
from gamechangerml.src.utilities.es_utils import ESUtils
from gamechangerml.api.fastapi.model_config import Config
from gamechangerml.api.fastapi.version import __version__

from gamechangerml.api.fastapi.settings import (
    logger,
    TOPICS_MODEL,
    CORPUS_DIR,
    QEXP_JBOOK_MODEL_NAME,
    QEXP_MODEL_NAME,
    WORD_SIM_MODEL,
    LOCAL_TRANSFORMERS_DIR,
    SENT_INDEX_PATH,
    latest_intel_model_encoder,
    latest_intel_model_sim,
    latest_doc_compare_encoder,
    latest_doc_compare_sim,
    DOC_COMPARE_SENT_INDEX_PATH,
    S3_CORPUS_PATH,
    QA_MODEL,
    ignore_files,
)

from gamechangerml.api.utils.threaddriver import MlThread
from gamechangerml.train.pipeline import Pipeline
from gamechangerml.api.utils import processmanager
from gamechangerml.api.fastapi.model_loader import ModelLoader
from gamechangerml.src.utilities.test_utils import (
    collect_evals,
    handle_sent_evals,
)
from gamechangerml import MODEL_PATH
from gamechangerml.src.utilities import gc_web_api

router = APIRouter()
MODELS = ModelLoader()
gcClient = gc_web_api.GCWebClient()
## Get Methods ##

pipeline = Pipeline()
es = ESUtils()


@router.get("/")
async def api_information():
    return {
        "API_Name": "GAMECHANGER ML API",
        "Version": __version__,
        "Elasticsearch_Host": es.root_url,
        "Elasticsearch_Status": get_es_status(),
    }


def get_es_status():
    status = "red"
    try:
        res = es.get(es.root_url + "_cluster/health", timeout=5)
        cont = json.loads(res.content)
        status = cont["status"]
    except Exception as e:
        logger.warning(e)

    return status


@router.get("/getProcessStatus")
async def get_process_status():
    return {
        "process_status": processmanager.PROCESS_STATUS.value,
        "completed_process": processmanager.COMPLETED_PROCESS.value,
    }


@router.get("/getDataList")
def get_downloaded_data_list():
    """
    Gets a list of the data in the local data folder
    Args:
    Returns: dict {"dirs":[ array of dicts {"name":(name of file):"path":(base directory), "files":(arr of files in directory),"subdirectories":(arr of subdirectories)}]}
    """
    files = []
    dir_arr = []
    logger.info(DATA_PATH)

    for dir in os.listdir(DATA_PATH):
        temp_path = os.path.join(DATA_PATH, dir)
        if os.path.isdir(temp_path):
            for dirpath, dirnames, filenames in os.walk(temp_path):
                dir_arr.append(
                    {
                        "name": dirpath.replace(temp_path, ""),
                        "path": dir,
                        "files": filenames,
                        "subdirectories": dirnames,
                    }
                )

    return {"dirs": dir_arr}


@router.get("/getModelsList")
def get_downloaded_models_list():
    """
    Gets a list of the models in the local model folder
    Args:
    Returns:{
        "transformers": (list of transformers),
        "sentence": (list of sentence indexes),
        "qexp": (list of query expansion indexes),
        "ltr": (list of learn to rank),
    }
    """
    qexp_list = {}
    jbook_qexp_list = {}
    sent_index_list = {}
    transformer_list = {}
    topic_models = {}
    ltr_list = {}
    # QEXP MODEL PATH
    try:
        for f in os.listdir(Config.LOCAL_PACKAGED_MODELS_DIR):
            if ("qexp_" in f) and ("tar" not in f):
                qexp_list[f] = {}
                meta_path = os.path.join(
                    Config.LOCAL_PACKAGED_MODELS_DIR, f, "metadata.json"
                )
                if os.path.isfile(meta_path):
                    meta_file = open(meta_path)
                    qexp_list[f] = json.load(meta_file)
                    qexp_list[f]["evaluation"] = {}
                    qexp_list[f]["evaluation"] = collect_evals(
                        os.path.join(Config.LOCAL_PACKAGED_MODELS_DIR, f)
                    )
                    meta_file.close()
    except Exception as e:
        logger.error(e)
        logger.info("Cannot get QEXP model path")
    # JBOOK QEXP
    try:
        for f in os.listdir(Config.LOCAL_PACKAGED_MODELS_DIR):
            if ("jbook_qexp_" in f) and ("tar" not in f):
                jbook_qexp_list[f] = {}
                meta_path = os.path.join(
                    Config.LOCAL_PACKAGED_MODELS_DIR, f, "metadata.json"
                )
                if os.path.isfile(meta_path):
                    meta_file = open(meta_path)
                    jbook_qexp_list[f] = json.load(meta_file)
                    jbook_qexp_list[f]["evaluation"] = {}
                    jbook_qexp_list[f]["evaluation"] = collect_evals(
                        os.path.join(Config.LOCAL_PACKAGED_MODELS_DIR, f)
                    )
                    meta_file.close()
    except Exception as e:
        logger.error(e)
        logger.info("Cannot get QEXP model path")

    # TRANSFORMER MODEL PATH
    try:
        for trans in os.listdir(LOCAL_TRANSFORMERS_DIR.value):
            if trans not in ignore_files and "." not in trans:
                transformer_list[trans] = {}
                config_path = os.path.join(
                    LOCAL_TRANSFORMERS_DIR.value, trans, "config.json"
                )
                if os.path.isfile(config_path):
                    config_file = open(config_path)
                    transformer_list[trans] = json.load(config_file)
                    transformer_list[trans]["evaluation"] = {}
                    transformer_list[trans]["evaluation"] = handle_sent_evals(
                        os.path.join(LOCAL_TRANSFORMERS_DIR.value, trans)
                    )
                    config_file.close()
    except Exception as e:
        logger.error(e)
        logger.info("Cannot get JBook model path")
    # SENTENCE INDEX
    # get largest file name with sent_index prefix (by date)
    try:
        for f in os.listdir(Config.LOCAL_PACKAGED_MODELS_DIR):
            if ("sent_index" in f) and ("tar" not in f):
                logger.info(f"sent indices: {str(f)}")
                sent_index_list[f] = {}
                meta_path = os.path.join(
                    Config.LOCAL_PACKAGED_MODELS_DIR, f, "metadata.json"
                )
                if os.path.isfile(meta_path):
                    meta_file = open(meta_path)
                    sent_index_list[f] = json.load(meta_file)
                    sent_index_list[f]["evaluation"] = {}

                    sent_index_list[f]["evaluation"] = handle_sent_evals(
                        os.path.join(Config.LOCAL_PACKAGED_MODELS_DIR, f)
                    )
                    meta_file.close()
    except Exception as e:
        logger.error(e)
        logger.info("Cannot get Sentence Index model path")

    # TOPICS MODELS
    try:

        topic_dirs = [
            name
            for name in os.listdir(Config.LOCAL_PACKAGED_MODELS_DIR)
            if os.path.isdir(os.path.join(Config.LOCAL_PACKAGED_MODELS_DIR, name))
            and "topic_model_" in name
        ]
        for topic_model_name in topic_dirs:
            topic_models[topic_model_name] = {}
            try:
                with open(
                    os.path.join(
                        Config.LOCAL_PACKAGED_MODELS_DIR,
                        topic_model_name,
                        "metadata.json",
                    )
                ) as mf:
                    topic_models[topic_model_name] = json.load(mf)
            except Exception as e:
                logger.error(e)
                topic_models[topic_model_name] = {
                    "Error": "Failed to load metadata file for this model"
                }

    except Exception as e:
        logger.error(e)
        logger.info("Cannot get Topic model path")

    # LTR
    try:
        for f in os.listdir(Config.LOCAL_PACKAGED_MODELS_DIR):
            if ("ltr" in f) and ("tar" not in f):
                logger.info(f"LTR: {str(f)}")
                ltr_list[f] = {}
                meta_path = os.path.join(
                    Config.LOCAL_PACKAGED_MODELS_DIR, f, "metadata.json"
                )
                if os.path.isfile(meta_path):
                    meta_file = open(meta_path)
                    ltr_list[f] = json.load(meta_file)
                    meta_file.close()
    except Exception as e:
        logger.error(e)
        logger.info("Cannot get Sentence Index model path")

    model_list = {
        "transformers": transformer_list,
        "sentence": sent_index_list,
        "qexp": qexp_list,
        "jbook_qexp": jbook_qexp_list,
        "topic_models": topic_models,
        "ltr": ltr_list,
    }
    return model_list


@router.post("/deleteLocalModel")
async def delete_local_model(model: dict, response: Response):
    """
    Delete a model from the local model folder
    Args: model: dict; {"model":(model you want to delete), "type":(type of model being deleted)}
    Returns: process statuses
    """

    def removeDirectory(dir):
        try:
            logger.info(
                f'Removing directory {os.path.join(dir,model["model"])}')
            shutil.rmtree(os.path.join(dir, model["model"]))
        except OSError as e:
            logger.error(e)

    def removeFiles(dir):
        for f in os.listdir(dir):
            if model["model"] in f:
                logger.info(f"Removing file {f}")
                try:
                    os.remove(os.path.join(dir, f))
                except OSError as e:
                    logger.error(e)

    logger.info(model)
    if model["type"] == "transformers":
        removeDirectory(LOCAL_TRANSFORMERS_DIR.value)
    elif model["type"] in ("sentence", "qexp", "doc_compare_sentence"):
        removeDirectory(Config.LOCAL_PACKAGED_MODELS_DIR)
        removeFiles(Config.LOCAL_PACKAGED_MODELS_DIR)

    return await get_process_status()


@router.get("/LTR/initLTR", status_code=200)
async def initLTR(response: Response):
    """generate judgement - checks how many files are in the corpus directory
    Args:
    Returns: integer
    """
    number_files = 0
    resp = None
    try:
        pipeline.init_ltr()
    except Exception as e:
        logger.warning("Could not init LTR")
    return resp


@router.get("/LTR/createModel", status_code=200)
async def create_LTR_model(response: Response):
    """generate judgement - checks how many files are in the corpus directory
    Args:
    Returns: integer
    """
    number_files = 0
    resp = None
    model = []

    def ltr_process():
        try:

            pipeline.create_ltr()
            processmanager.update_status(
                processmanager.ltr_creation,
                1,
                1,
                thread_id=threading.current_thread().ident,
            )
        except Exception as e:
            logger.warning(e)
            logger.warning(f"There is an issue with LTR creation")
            response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            processmanager.update_status(
                processmanager.ltr_creation,
                failed=True,
                thread_id=threading.current_thread().ident,
            )

    ltr_thread = MlThread(ltr_process)
    ltr_thread.start()
    processmanager.running_threads[ltr_thread.ident] = ltr_thread
    processmanager.update_status(
        processmanager.ltr_creation, 0, 1, thread_id=ltr_thread.ident
    )

    return response.status_code


@router.get("/getFilesInCorpus", status_code=200)
async def files_in_corpus(response: Response):
    """files_in_corpus - checks how many files are in the corpus directory
    Args:
    Returns: integer
    """
    number_files = 0
    try:
        logger.info("Reading files from local corpus")
        number_files = len(
            [
                name
                for name in os.listdir(CORPUS_DIR)
                if os.path.isfile(os.path.join(CORPUS_DIR, name))
            ]
        )
    except:
        logger.warning(f"Could not get files in corpus")
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    return json.dumps(number_files)


@router.get("/getLoadedModels")
async def get_current_models():
    """get_current_models - endpoint for current models
    Args:
    Returns:
        dict of model name
    """
    # sent_model = latest_intel_model_sent.value
    return {
        "sim_model": latest_intel_model_sim.value,
        "encoder_model": latest_intel_model_encoder.value,
        "sentence_index": SENT_INDEX_PATH.value,
        "qexp_model": QEXP_MODEL_NAME.value,
        "jbook_model": QEXP_JBOOK_MODEL_NAME.value,
        "topic_model": TOPICS_MODEL.value,
        "wordsim_model": WORD_SIM_MODEL.value,
        "qa_model": QA_MODEL.value,
        "doc_compare_sim_model": latest_doc_compare_sim.value,
        "doc_compare_encoder_model": latest_doc_compare_encoder.value,
        "doc_compare_sentence_index": DOC_COMPARE_SENT_INDEX_PATH.value,
    }


@router.get("/download", status_code=200)
async def download(response: Response):
    """download - downloads dependencies from s3
    Args:
    Returns:
    """

    def download_s3_thread():
        try:
            logger.info("Attempting to download dependencies from S3")
            output = subprocess.call(
                ["gamechangerml/scripts/download_dependencies.sh"])
            # get_transformers(overwrite=False)
            # get_sentence_index(overwrite=False)
            processmanager.update_status(
                processmanager.s3_dependency,
                1,
                1,
                thread_id=threading.current_thread().ident,
            )
        except:

            logger.warning(f"Could not get dependencies from S3")
            response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            processmanager.update_status(
                processmanager.s3_dependency,
                failed=True,
                thread_id=threading.current_thread().ident,
            )

    thread = MlThread(download_s3_thread)
    thread.start()
    processmanager.running_threads[thread.ident] = thread
    processmanager.update_status(
        processmanager.s3_dependency, 0, 1, thread_id=thread.ident
    )
    return await get_process_status()


@router.post("/downloadS3File", status_code=200)
async def download_s3_file(file_dict: dict, response: Response):
    """
    download a s3 file from the given path. If folder is given download all files recursively from the folder and untar all .tar files
    Args:file_dict - dict {"file":(file or folder path),"type":"whether from ml-data or models)}
    Returns: process status
    """

    def download_s3_thread():
        logger.info(f'downloading file {file_dict["file"]}')
        try:

            path = (
                "gamechangerml/models/"
                if file_dict["type"] == "models"
                else "gamechangerml/"
            )
            downloaded_files = utils.get_model_s3(
                file_dict["file"], f"bronze/gamechanger/{file_dict['type']}/", path
            )
            logger.info(downloaded_files)

            if len(downloaded_files) == 0:
                processmanager.update_status(
                    f's3: {file_dict["file"]}',
                    failed=True,
                    message="No files found",
                    thread_id=threading.current_thread().ident,
                )
                return

            processmanager.update_status(
                f's3: {file_dict["file"]}',
                0,
                len(downloaded_files),
                thread_id=threading.current_thread().ident,
            )
            i = 0
            for f in downloaded_files:
                i += 1
                processmanager.update_status(
                    f's3: {file_dict["file"]}',
                    0,
                    i,
                    thread_id=threading.current_thread().ident,
                )
                logger.info(f)
                if ".tar" in f:
                    tar = tarfile.open(f)
                    if tar.getmembers()[0].name == ".":
                        if "sentence_index" in file_dict["file"]:
                            path += "sent_index_"
                        elif "jbook_qexp_model" in file_dict["file"]:
                            path += "jbook_qexp_"
                        elif "qexp_model" in file_dict["file"]:
                            path += "qexp_"
                        elif "topic_model" in file_dict["file"]:
                            path += "topic_models"

                        path += f.split("/")[-1].split(".")[0]

                    logger.info(f"Extracting {f} to {path}")
                    tar.extractall(
                        path=path,
                        members=[
                            member
                            for member in tar.getmembers()
                            if (
                                ".git" not in member.name
                                and ".DS_Store" not in member.name
                            )
                        ],
                    )
                    tar.close()

            processmanager.update_status(
                f's3: {file_dict["file"]}',
                len(downloaded_files),
                len(downloaded_files),
                thread_id=threading.current_thread().ident,
            )

        except PermissionError:
            failedExtracts = []
            for member in tar.getmembers():
                try:
                    tar.extract(member, path=path)
                except Exception as e:
                    failedExtracts.append(member.name)

            logger.warning(
                f"Could not extract {failedExtracts} with permission errors")
            processmanager.update_status(
                f's3: {file_dict["file"]}',
                failed=True,
                message="Permission error not all files extracted",
                thread_id=threading.current_thread().ident,
            )

        except Exception as e:
            logger.warning(e)
            logger.warning(f"Could download {file_dict['file']} from S3")
            response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            processmanager.update_status(
                f's3: {file_dict["file"]}',
                failed=True,
                message=e,
                thread_id=threading.current_thread().ident,
            )

    thread = MlThread(download_s3_thread)
    thread.start()
    processmanager.running_threads[thread.ident] = thread
    processmanager.update_status(
        f's3: {file_dict["file"]}', 0, 1, thread_id=thread.ident
    )

    return await get_process_status()


@router.get("/s3", status_code=200)
async def s3_func(function, response: Response):
    """s3_func - s3 functionality for model managment
    Args:
        function: str
    Returns:
    """
    models = []
    try:
        logger.info("Retrieving model list from s3::")
        if function == "models":
            s3_path = "bronze/gamechanger/models/"
            models = utils.get_models_list(s3_path)
        elif function == "data":
            s3_path = "bronze/gamechanger/ml-data/"
            models = utils.get_models_list(s3_path)
    except:
        logger.warning(f"Could not get model list from s3")
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    return models


## Post Methods ##


@router.post("/reloadModels", status_code=200)
async def reload_models(model_dict: dict, response: Response):
    """load_latest_models - endpoint for updating the transformer model
    Args:
        model_dict: dict; {"sentence": "bert...",
            "qexp": "bert...", "transformer": "bert..."}
        Response: Response class; for status codes(apart of fastapi do not need to pass param)
    Returns:
    """
    try:
        total = len(model_dict)

        # put the reload process on a thread
        def reload_thread(model_dict):
            try:
                progress = 0
                thread_name = processmanager.reloading + " ".join(
                    [key for key in model_dict]
                )
                logger.info(thread_name)
                if "sentence" in model_dict:
                    sentence_path = os.path.join(
                        Config.LOCAL_PACKAGED_MODELS_DIR, model_dict["sentence"]
                    )
                    # uses SENT_INDEX_PATH by default
                    logger.info("Attempting to load Sentence Transformer")
                    MODELS.initSentenceSearcher(sentence_path)
                    SENT_INDEX_PATH.value = sentence_path
                    progress += 1
                    processmanager.update_status(
                        thread_name,
                        progress,
                        total,
                        thread_id=threading.current_thread().ident,
                    )
                if "doc_compare_sentence" in model_dict:
                    doc_compare_sentence_path = os.path.join(
                        Config.LOCAL_PACKAGED_MODELS_DIR, model_dict["doc_compare_sentence"]
                    )
                    # uses DOC_COMPARE_SENT_INDEX_PATH by default
                    logger.info(
                        "Attempting to load Doc Compare Sentence Transformer")
                    MODELS.initDocumentCompareSearcher(
                        doc_compare_sentence_path)
                    DOC_COMPARE_SENT_INDEX_PATH.value = doc_compare_sentence_path
                    progress += 1
                    processmanager.update_status(
                        thread_name,
                        progress,
                        total,
                        thread_id=threading.current_thread().ident,
                    )
                if "qexp" in model_dict:
                    qexp_name = os.path.join(
                        Config.LOCAL_PACKAGED_MODELS_DIR, model_dict["qexp"]
                    )
                    # uses QEXP_MODEL_NAME by default
                    logger.info("Attempting to load QE")
                    MODELS.initQE(qexp_name)
                    QEXP_MODEL_NAME.value = qexp_name
                    progress += 1
                    processmanager.update_status(
                        thread_name,
                        progress,
                        total,
                        thread_id=threading.current_thread().ident,
                    )
                if "jbook_qexp" in model_dict:
                    jbook_qexp_name = os.path.join(
                        Config.LOCAL_PACKAGED_MODELS_DIR, model_dict["jbook_qexp"]
                    )
                    # uses QEXP_MODEL_NAME by default
                    logger.info("Attempting to load Jbook QE")
                    MODELS.initQEJBook(jbook_qexp_name)
                    QEXP_JBOOK_MODEL_NAME.value = jbook_qexp_name
                    progress += 1
                    processmanager.update_status(
                        thread_name,
                        progress,
                        total,
                        thread_id=threading.current_thread().ident,
                    )

                if "topic_models" in model_dict:
                    topics_name = os.path.join(
                        Config.LOCAL_PACKAGED_MODELS_DIR, model_dict["topic_models"]
                    )

                    logger.info("Attempting to load Topics")
                    MODELS.initTopics(topics_name)
                    TOPICS_MODEL.value = topics_name
                    progress += 1
                    processmanager.update_status(
                        thread_name,
                        progress,
                        total,
                        thread_id=threading.current_thread().ident,
                    )
                if "qa_model" in model_dict:
                    qa_model_name = os.path.join(
                        Config.LOCAL_PACKAGED_MODELS_DIR, model_dict["qa_model"],
                    )

                    logger.info("Attempting to load QA model")
                    qa_model_name = qa_model_name.split("/")[-1]
                    MODELS.initQA(qa_model_name)
                    QA_MODEL.value = qa_model_name
                    progress += 1
                    processmanager.update_status(
                        thread_name,
                        progress,
                        total,
                        thread_id=threading.current_thread().ident,
                    )
            except Exception as e:
                logger.warning(e)
                processmanager.update_status(
                    f"{processmanager.reloading}",
                    failed=True,
                    thread_id=threading.current_thread().ident,
                )

        args = {"model_dict": model_dict}
        thread = MlThread(reload_thread, args)
        thread.start()
        processmanager.running_threads[thread.ident] = thread
        thread_name = processmanager.reloading + \
            " ".join([key for key in model_dict])
        processmanager.update_status(
            thread_name, 0, total, thread_id=thread.ident)
    except Exception as e:
        logger.warning(e)

    return await get_process_status()


@router.post("/downloadCorpus", status_code=200)
async def download_corpus(corpus_dict: dict, response: Response):
    """load_latest_models - endpoint for updating the transformer model
    Args:
        model_dict: dict; {"sentence": "bert...",
            "qexp": "bert...", "transformer": "bert..."}
        Response: Response class; for status codes(apart of fastapi do not need to pass param)
    Returns:
    """
    try:
        logger.info("Attempting to download corpus from S3")
        # grabs the s3 path to the corpus from the post in "corpus"
        # then passes in where to dowload the corpus locally.

        s3_corpus_dir = corpus_dict.get("corpus", S3_CORPUS_PATH)
        args = {"s3_corpus_dir": s3_corpus_dir, "output_dir": CORPUS_DIR}

        logger.info(args)
        corpus_thread = MlThread(utils.get_s3_corpus, args)
        corpus_thread.start()
        processmanager.running_threads[corpus_thread.ident] = corpus_thread
        processmanager.update_status(
            processmanager.corpus_download, 0, 1, thread_id=corpus_thread.ident
        )
    except Exception as e:
        logger.warning(f"Could not get corpus from S3")
        logger.warning(e)
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        processmanager.update_status(
            processmanager.corpus_download,
            failed=True,
            message=e,
            thread_id=corpus_thread.ident,
        )

    return await get_process_status()


# Create a mapping between the training methods and input from the api
# Methods for all the different models we can train
# Defined outside the function so they arent recreated each time its called

# Methods for all the different models we can train


def update_metadata(model_dict):
    logger.info("Attempting to update feature metadata")
    pipeline = Pipeline()
    model_dict["build_type"] = "meta"
    try:
        corpus_dir = model_dict["corpus_dir"]
    except:
        corpus_dir = CORPUS_DIR
    try:
        retriever = MODELS.sentence_searcher
        logger.info("Using pre-loaded SentenceSearcher")
    except:
        retriever = None
        logger.info("Setting SentenceSearcher to None")
    try:
        meta_steps = model_dict["meta_steps"]
    except:
        meta_steps = [
            "pop_docs",
            "combined_ents",
            "rank_features",
            "update_sent_data",
        ]
    try:
        index_path = model_dict["index_path"]
    except:
        index_path = os.path.join(
            Config.LOCAL_PACKAGED_MODELS_DIR, model_dict["sentence"]
        )
    try:
        update_eval_data = model_dict["update_eval_data"]
    except:
        update_eval_data = False
    try:
        testing_only = model_dict["testing_only"]
    except:
        testing_only = False
    try:
        upload = model_dict["upload"]
    except:
        upload = True

    logger.info(f"Testing only is set to: {testing_only}")

    args = {
        "meta_steps": meta_steps,
        "corpus_dir": corpus_dir,
        "retriever": retriever,
        "index_path": index_path,
        "update_eval_data": update_eval_data,
        "testing_only": testing_only,
        "upload": upload,
    }

    pipeline.run(
        build_type=model_dict["build_type"],
        run_name=datetime.now().strftime("%Y%m%d"),
        params=args,
    )


def finetune_sentence(model_dict):
    logger.info("Attempting to finetune the sentence transformer")
    try:
        testing_only = model_dict["testing_only"]
    except:
        testing_only = False
    try:
        remake_train_data = model_dict["remake_train_data"]
    except:
        remake_train_data = False
    try:
        model = model_dict["model"]
    except:
        model = None
    args = {
        "batch_size": 8,
        "epochs": int(model_dict["epochs"]),
        "warmup_steps": int(model_dict["warmup_steps"]),
        "testing_only": bool(testing_only),
        "remake_train_data": bool(remake_train_data),
        "retriever": MODELS.sentence_searcher,
        "model": model,
    }
    pipeline.run(
        build_type="sent_finetune",
        run_name=datetime.now().strftime("%Y%m%d"),
        params=args,
    )


def train_sentence(model_dict):

    build_type = model_dict["build_type"]
    logger.info(f"Attempting to start {build_type} pipeline")

    corpus_dir = model_dict.get("corpus_dir", CORPUS_DIR)
    if not os.path.exists(corpus_dir):
        logger.warning(f"Corpus is not in local directory {str(corpus_dir)}")
        raise Exception("Corpus is not in local directory")
    args = {
        "corpus": corpus_dir,
        "encoder_model": model_dict["encoder_model"],
        "gpu": bool(model_dict["gpu"]),
        "upload": bool(model_dict["upload"]),
        "version": model_dict["version"],
    }
    logger.info(args)
    pipeline.run(
        build_type=model_dict["build_type"],
        run_name=datetime.now().strftime("%Y%m%d"),
        params=args,
    )


def train_qexp(model_dict):
    logger.info("Attempting to start qexp pipeline")
    args = {
        "upload": bool(model_dict["upload"]),
        "version": model_dict["version"],
    }
    pipeline.run(
        build_type=model_dict["build_type"],
        run_name=datetime.now().strftime("%Y%m%d"),
        params=args,
    )


def run_evals(model_dict):
    logger.info("Attempting to run evaluation")
    try:
        sample_limit = int(model_dict["sample_limit"])
    except:
        sample_limit = 15000
    if "sent_index" in model_dict["model_name"]:
        retriever = MODELS.sentence_searcher
    else:
        retriever = None
    args = {
        "model_name": model_dict["model_name"],
        "eval_type": model_dict["eval_type"],
        "sample_limit": sample_limit,
        "validation_data": model_dict["validation_data"],
        "retriever": retriever,
    }
    pipeline.run(
        build_type=model_dict["build_type"],
        run_name=datetime.now().strftime("%Y%m%d"),
        params=args,
    )


def train_topics(model_dict):
    logger.info("Attempting to train topic model")
    logger.info(model_dict)
    args = {"sample_rate": model_dict["sample_rate"],
            "upload": model_dict["upload"]}
    pipeline.run(
        build_type=model_dict["build_type"],
        run_name=datetime.now().strftime("%Y%m%d"),
        params=args,
    )


@router.post("/trainModel", status_code=200)
async def train_model(model_dict: dict, response: Response):
    """load_latest_models - endpoint for updating the transformer model
    Args:
        model_dict: dict; {"encoder_model":"msmarco-distilbert-base-v2", "gpu":true, "upload":false,"version": "v5"}
        Response: Response class; for status codes(apart of fastapi do not need to pass param)
    Returns:
    """
    try:
        # Create a mapping between the training methods and input from the api
        training_switch = {
            "sentence": train_sentence,
            "qexp": train_qexp,
            "sent_finetune": finetune_sentence,
            "eval": run_evals,
            "meta": update_metadata,
            "topics": train_topics,
        }

        # Set the training method to be loaded onto the thread
        if "build_type" in model_dict and model_dict["build_type"] in training_switch:
            training_method = training_switch[model_dict["build_type"]]
        else:  # PLACEHOLDER
            logger.warn(
                "No build type specified in model_dict, defaulting to sentence")
            model_dict["build_type"] = "sentence"
            training_method = training_switch[model_dict["build_type"]]

        build_type = model_dict.get("build_type")
        training_method = training_switch.get(build_type)

        if not training_method:
            raise Exception(
                f"No training method mapped for build type {build_type}")

        # Set the training method to be loaded onto the thread
        training_thread = MlThread(training_method, args={
                                   "model_dict": model_dict})
        training_thread.start()
        processmanager.running_threads[training_thread.ident] = training_thread
        processmanager.update_status(
            processmanager.training, 0, 1, thread_id=training_thread.ident
        )
    except:
        logger.warning(f"Could not train/evaluate the model")
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        processmanager.update_status(
            processmanager.training, failed=True, thread_id=training_thread.ident
        )

    return await get_process_status()


@router.post("/stopProcess")
async def stop_process(thread_dict: dict, response: Response):
    """stop_process - endpoint for stopping a process in a thread
    Args:
        thread_dict: dict; {"thread_id":(int of thread id), "process":(name of the process so we can also update it in redis)}
        Response: Response class; for status codes(apart of fastapi do not need to pass param)
    Returns:
        Stopped thread id
    """
    logger.info(processmanager.running_threads)
    thread_id = int(thread_dict["thread_id"])
    with processmanager.thread_lock:
        if thread_id in processmanager.running_threads:
            processmanager.running_threads[thread_id].kill()
            del processmanager.running_threads[thread_id]
    processmanager.update_status(
        thread_dict["process"],
        failed=True,
        message="Killed by user",
        thread_id=thread_id,
    )

    return {"stopped": thread_id}


@router.post("/sendUserAggregations")
async def get_user_data(data_dict: dict, response: Response):
    """get_user_data - Get user aggregation data for selected date and write to data folder
    Args:
        date_dict: dict; {data}
        Response: Response class; for status codes(apart of fastapi do not need to pass param)
    Returns:
        confirmation of data download
    """

    userData = data_dict["params"]["userData"]
    GC_USER_DATA = os.path.join(
        DATA_PATH, "user_data", "search_history", "UserAggregations.json"
    )
    with open(GC_USER_DATA, "w") as f:
        json.dump(userData, f)

    searchData = data_dict["params"]["searchData"]
    df = pd.DataFrame(searchData)
    GC_SEARCH_DATA = os.path.join(
      DATA_PATH, "user_data", "search_history","SearchPdfMapping.csv"
    )
    df.to_csv(GC_SEARCH_DATA)

    return f"wrote {len(userData)} user data and searches to file"
