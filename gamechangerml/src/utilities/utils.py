import logging
from os import rename, makedirs, listdir
from os.path import join, isdir, basename
import glob
import tarfile
import typing as t
from pathlib import Path
from gamechangerml.configs import S3Config
from gamechangerml import REPO_PATH, MODEL_PATH
from gamechangerml.src.services import S3Service

logger = logging.getLogger("gamechanger")

def get_local_model_prefix(prefix: str, folder: str = MODEL_PATH):
    """get_local_model_prefix: gets all folders or models with the prefix, i.e. sent_index
    folder: PATH folder of models
    prefix: string of model name i.e. sent_index
    returns: list of names
    """
    return [
        filename
        for filename in listdir(folder)
        if filename.startswith(prefix) and "tar" not in filename
    ]

def create_model_schema(model_dir, file_prefix):
    num = 0
    while isdir(join(model_dir, file_prefix)):
        file_prefix = f"{file_prefix.split('_')[0]}_{num}"
        num += 1
    
    dirpath = join(model_dir, file_prefix)
    makedirs(dirpath)

    logger.info(f"Created directory: {dirpath}.")


def get_transformers(model_path="transformers_v4/transformers.tar", overwrite=False, bucket=None):
    if bucket is None:
        bucket = S3Service.connect_to_bucket(S3Config.BUCKET_NAME, logger)

    models_path = join(REPO_PATH, "gamechangerml/models")
    try:
        if glob.glob(join(models_path, "transformer*")):
            if not overwrite:
                print(
                    "transformers exists -- not pulling from s3, specify overwrite = True"
                )
                return
        for obj in bucket.objects.filter(Prefix=model_path):
            print(obj)
            bucket.download_file(
                obj.key, join(models_path, obj.key.split("/")[-1])
            )
            compressed = obj.key.split("/")[-1]
        cache_path = join(models_path, compressed)
        print("uncompressing: " + cache_path)
        compressed_filename = compressed.split(".tar")[0]
        if isdir(f"{models_path}/{compressed_filename}"):
            rename(
                f"{models_path}/{compressed_filename}",
                f"{models_path}/{compressed_filename}_backup",
            )
        tar = tarfile.open(cache_path)
        tar.extractall(models_path)
        tar.close()
    except Exception:
        print("cannot get transformer model")
        raise


def get_sentence_index(model_path="sent_index/", overwrite=False, bucket=None):
    if bucket is None:
        bucket = S3Service.connect_to_bucket(S3Config.BUCKET_NAME, logger)

    models_path = join(REPO_PATH, "gamechangerml/models")
    try:
        if glob.glob(join(models_path, "sent_index*")):
            if not overwrite:
                print(
                    "sent_index exists -- not pulling from s3, specify overwrite = True"
                )
                return
        for obj in bucket.objects.filter(Prefix=model_path):
            print(obj)
            bucket.download_file(
                obj.key, join(models_path, obj.key.split("/")[-1])
            )
            compressed = obj.key.split("/")[-1]
        cache_path = join(models_path, compressed)
        print("uncompressing: " + cache_path)
        compressed_filename = compressed.split(".tar")[0]
        if isdir(f"{models_path}/{compressed_filename}"):
            rename(
                f"{models_path}/{compressed_filename}",
                f"{models_path}/{compressed_filename}_backup",
            )
        tar = tarfile.open(cache_path)
        tar.extractall(models_path)
        tar.close()
    except Exception:
        print("cannot get transformer model")
        raise


def create_tgz_from_dir(
    src_dir: t.Union[str, Path],
    dst_archive: t.Union[str, Path],
) -> None:
    with tarfile.open(dst_archive, "w:gz") as tar:
        tar.add(src_dir, arcname=basename(src_dir))
