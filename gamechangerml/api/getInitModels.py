"""THIS FILE INTENDED TO BE RUN BY startProd/Dev.sh AS A MODULE"""

from threading import Thread
from datetime import datetime
from time import sleep
from os import environ, makedirs
from os.path import join, exists

from gamechangerml.api.fastapi.model_config import Config
from gamechangerml.src.data_transfer import get_latest_model_name
from gamechangerml.src.services import S3Service
from gamechangerml.configs import S3Config
from gamechangerml.src.utilities import configure_logger


def poll_alive():
    while True:
        sleep(3)
        print("{} getInitModels.py still running...".format(datetime.now()))

def start_thread():
    thread = Thread(target=poll_alive)
    thread.daemon = True
    thread.start()

def verify_env_var(value, name):
    """Verify that an environment variable is not None.

    Args:
        value (any): Check that this value is not None
        name (str): Name of the environment variable

    Raises:
        RuntimeError: If value is None.
    """
    if value is None:
        raise RuntimeError(f"{name} cannot be None. Verify env setup.")
    
def run(pull_type, logger):
    """Main function to run for getInitModels.py.

    Args:
        pull_type (str): The name of the model to pull. Or, 
            "all": to pull all models
            "latest": to pull the latest model

    Raises:
        Exception: If S3 download fails

    Returns:
        (list of str, list of str): A tuple of length 2 with:
            downloaded_paths: S3 paths of files successfully downloaded
            existing_paths: local paths for files that were not downloaded 
                because they already exist
    """
    start_thread()

    S3_MODELS_DIR = Config.S3_MODELS_DIR
    LOCAL_MODELS_DIR = Config.LOCAL_PACKAGED_MODELS_DIR
    verify_env_var(LOCAL_MODELS_DIR, "LOCAL_MODELS_DIR")

    bucket = S3Service.connect_to_bucket(S3Config.BUCKET_NAME, logger)
    
    logger.info("pull_type:", pull_type)
    if pull_type == "all":
        model_names = S3Service.get_object_names(bucket, S3_MODELS_DIR, "dir")
    elif pull_type == "latest":
        model_names = get_latest_model_name(S3_MODELS_DIR, bucket)
        if model_names is None:
            logger.error("No latest model detected.")
            exit(1)
        model_names = [model_names]
    else:
        model_names = [pull_type]

    downloaded_paths = []
    existing_paths = []

    for model_pkg in model_names:
        local_dir = join(LOCAL_MODELS_DIR, model_pkg)
        makedirs(local_dir, exist_ok=True)
        prefix = join(S3_MODELS_DIR, model_pkg)
        s3_file_names = S3Service.get_object_names(bucket, prefix, "filename")

        for fn in s3_file_names:
            s3_path = join(prefix, fn)
            try:
                local_file = join(local_dir, fn)
                if exists(local_file):
                    existing_paths.append(local_file)
                    logger.info(
                        f"{fn} already exists locally in {local_dir}. "
                        "Skipping download."
                    )
                else:
                    logger.info(f"Downloading from S3: {s3_path}")
                    S3Service.download(bucket, s3_path, local_dir, logger)
                    downloaded_paths.append(s3_path)
            except Exception as e:
                logger.exception(
                    f"Failed to download from S3: {s3_path}."
                )
                raise e
    
    return downloaded_paths, existing_paths

    
if __name__ == "__main__":
    logger = configure_logger(min_level="INFO")
    logger.info("Running getInitModels.py")
    
    pull_type = environ.get("PULL_MODELS")

    try:
        downloaded, existing = run(pull_type, logger)
    except Exception:
        logger.exception("----- FATAL ERROR ON INIT, FETCHING MODELS FAILED.")
        exit(1)
    else:
        logger.info("++++ Model retrieval success")
        logger.info(f"Downloaded: {downloaded}.")
        logger.info(f"Not downloaded (already exist): {existing}.")
        exit(0)
    
        
   