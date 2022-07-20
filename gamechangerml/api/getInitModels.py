from threading import Thread
from datetime import datetime
from time import sleep
import logging
import os
from gamechangerml.api.fastapi.model_config import Config
from gamechangerml.src.utilities.utils import (
    download_models,
    download_latest_model_package,
)


# THIS FILE INTENDED TO BE RUN BY startProd/Dev.sh AS A MODULE


def poll_alive():
    while True:
        sleep(3)
        print("{} getInitModels.py still running...".format(datetime.now()))


if __name__ == "__main__":
    try:
        print("Running getInitModels.py")
        thread = Thread(target=poll_alive)
        thread.daemon = True
        thread.start()
        s3_models_path = Config.S3_MODELS_DIR

        print(f"Downloading latest packaged model from {s3_models_path}")
        pull_type = os.environ.get("PULL_MODELS")
        if pull_type == "all":
            model_name = download_models(
                s3_models_path,
                Config.LOCAL_PACKAGED_MODELS_DIR,
                select="all",
            )
            print(f"Retrieved the following: {model_name}")
        elif pull_type == "latest":
            model_name = download_latest_model_package(
                s3_models_path, Config.LOCAL_PACKAGED_MODELS_DIR
            )
            print(f"Retrieved the following: {model_name}")
        else:
            print("Expecting a model...")
            print(f"Attempt to get {pull_type}")
            model_name = download_models(
                s3_models_path,
                Config.LOCAL_PACKAGED_MODELS_DIR,
                select=pull_type,
            )
        print("++++ Model retrieval success")
        exit(0)
    except Exception as e:
        print("\n ----- FATAL ERROR ON INIT, FETCHING MODELS FAILED \n")
        print(e)
        exit(1)
