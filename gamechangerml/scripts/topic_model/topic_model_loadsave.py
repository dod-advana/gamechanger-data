from gamechangerml import REPO_PATH
from gamechangerml.src.services import S3Service
from gamechangerml.configs import S3Config
from gamechangerml.src.utilities import configure_logger
from os import chdir, listdir
from os.path import join
import sys


S3_MODELS_DIR = "models/topic_models/"
TOPIC_MODEL_DIR = join(
    REPO_PATH, "gamechangerml/models/topic_models/models/"
)

def run():
    LOGGER = configure_logger(min_level="INFO")
    BUCKET = S3Service.connect_to_bucket(S3Config.BUCKET_NAME, LOGGER)

    if BUCKET is None:
        raise Exception("Failed to connect to S3 Bucket.")

    if ARG == "load":
        LOGGER.info("Downloading models from S3")
        start_char = len(S3_MODELS_DIR)
        for obj in BUCKET.objects.filter(Prefix=S3_MODELS_DIR):
            filename = obj.key[start_char:]
            LOGGER.info(f"Downloading {filename}.")
            S3Service.download(BUCKET, join(S3_MODELS_DIR, filename), "", LOGGER)
    elif ARG == "save":
        LOGGER.info("Saving models to S3.")
        upload_files = listdir()
        if not upload_files:
            raise Exception(
                f"No model files to upload. Load files into {TOPIC_MODEL_DIR}."
            )
        for f in upload_files:
            LOGGER.info(f"Saving {f}.")
            S3Service.upload_file(BUCKET, f, S3_MODELS_DIR + f, LOGGER)

    LOGGER.info("Finished")


if __name__ == "__main__":
    chdir(TOPIC_MODEL_DIR)

    arg_options = ["load", "save"]
    arg_msg = f"Argument must be one of {arg_options}"

    try:
        ARG = sys.argv[1].lower()
    except:
        raise Exception(arg_msg)
    else:
        if ARG not in arg_options:
            raise Exception(arg_msg)

    run()
