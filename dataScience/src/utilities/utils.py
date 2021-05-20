# package imports
# import gensim
import logging
import os
import shutil
from pathlib import Path
import glob
import zipfile
import tarfile
import boto3
from dataScience.src.utilities.aws_helper import *
from dataScience.configs.config import S3Config

logger = logging.getLogger("gamechanger")


def store_model_s3(data, s3_model_dir, filename):
    """
    store_model_s3 - write to s3 bucket
        params: data (binary), filename (without ext)
        output:
    """
    bucket = s3_connect()
    try:
        bucket.put_object(Body=data, Key=f"{s3_model_dir}" + filename)
    except:
        logger.debug(filename + " failed to store in S3")


def save_all_s3(models_path, model_name, s3_model_dir=S3Config.S3_MODELS_DIR):
    saved_models = [
        filename
        for filename in os.listdir(f"{models_path}/{model_name}")
        if filename.startswith(model_name)
    ]
    for fileName in saved_models:
        with open(f"{models_path}/{model_name}/{fileName}", mode="rb") as f:
            data = f.read()
            store_model_s3(data, s3_model_dir, f"{model_name}/{fileName}")
    logger.debug("Saved {model_name} files to S3")


def get_model_s3(filename, s3_model_dir):
    """
    read_model_s3 - read from s3 bucket
        params: filename (with ext)
        output:
    """
    bucket = s3_connect()
    model_path = os.path.join(s3_model_dir, filename)
    try:
        for obj in bucket.objects.filter(Prefix=model_path):
            print(obj.key)
            bucket.download_file(obj.key, obj.key.split("/")[-1])
    except RuntimeError:
        # print("cant download")
        logger.debug(filename + " failed to download from S3")


def store_corpus_s3(data, filename):
    """
    store_corpus_s3 - write to s3 bucket
        params: data (binary), filename (without ext)
        output:
    """
    bucket = s3_connect()
    try:
        bucket.put_object(Body=data, Key="corpus/" + filename)
    except RuntimeError:
        logger.debug(filename + " failed to store in S3")


def verify_model_name(model_dir, filePrefix):
    count = 0

    while os.path.isdir(os.path.join(model_dir, filePrefix)):
        filePrefix = filePrefix.split("_")[0]
        filePrefix = f"{filePrefix}_{count}"
        count = count + 1
    filePrefix = filePrefix.split("/")[-1]
    return filePrefix


def create_model_schema(model_dir, file_prefix):
    file_prefix = verify_model_name(model_dir, file_prefix)
    fulldir = f"{model_dir}/{file_prefix}"
    if not os.path.isdir(fulldir):
        try:
            os.mkdir(fulldir)
        except OSError:
            logger.error("Creation of directory %s failed" % fulldir)
        else:
            logger.info("Created directory %s" % fulldir)
    return file_prefix


def read_corpus_s3(filename, corpus_dir, output_dir="corpus"):
    """
    read_corpus_s3 - read from s3 bucket
        params: filename (with ext)
        output:
    """
    bucket = s3_connect()
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    try:
        bucket.download_file(
            f"{corpus_dir}/" + filename, os.path.join(output_dir, filename)
        )
    except RuntimeError:
        # print("cant download")
        logger.debug(filename + " failed to download from S3")


def get_s3_corpus_list():
    bucket = s3_connect()
    corp = []
    for obj in bucket.objects.filter(Prefix="corpus/"):
        corp.append(obj.key)

    return corp


def get_s3_corpus(corpus_dir):
    """
    not  recommended
    """
    bucket = s3_connect()
    corp = []
    path = corpus_dir
    try:
        os.mkdir(path)
    except OSError as error:
        print(error)
    for obj in bucket.objects.filter(Prefix=f"{corpus_dir}/"):
        corp.append(obj.key)
        print(obj.key)
        try:
            bucket.Object(obj.key).download_file(obj.key)
        except RuntimeError:
            logger.debug(f"Could not retrieve {obj.key}")
    return corp


def get_models_list(s3_models_dir):
    bucket = s3_connect()
    models = []
    for obj in bucket.objects.filter(Prefix=s3_models_dir):
        models.append((obj.key[len(s3_models_dir):], obj.last_modified))
    return models


def get_models_dict(models_list):
    models = {}
    for model in models_list:
        parts = model[0].rpartition("/")
        name = parts[0]
        kind = parts[2]
        if name not in models.keys():
            models[name] = []
        models[name].append(kind)
    print(models)
    return models


def get_latest_model_name(s3_models_dir):
    bucket = s3_connect()
    model_list = []
    for key in bucket.objects.filter(Prefix=s3_models_dir):
        model_list.append((key.key[len(s3_models_dir):], key.last_modified))
    sorted_models = sorted(model_list, key=lambda x: x[1])
    latest_model_name = sorted_models[-1][0].split("/")[0]
    return latest_model_name


def download_latest_model_package(s3_models_dir, local_packaged_models_dir):
    """download latest model package: this gets the MOST RECENT uploadted model
    ONLY from s3 model repo
    Args:
        s3_models_dir: s3 model directory. i.e. models/v3/
        local_packaged_models_dir: the local directory where models are stored.
    Returns:
        model_name: str - name of pulled down model
    """

    model_name = get_latest_model_name(s3_models_dir)
    if model_name in get_local_model_package_names(local_packaged_models_dir):
        logger.info("Latest model already available locally")
        if len(os.listdir(f"{local_packaged_models_dir}/{model_name}")) > 3:
            logger.info("Latest has all model files, nothing downloaded")
            return model_name

    bucket = s3_connect()
    package_dir = "{}/{}".format(local_packaged_models_dir, model_name)
    logger.debug("package dir {}".format(package_dir))

    if not os.path.isdir(package_dir):
        logger.debug("package dir does not exist")
        try:
            logger.debug("trying make dir")
            if not os.path.isdir(package_dir):
                os.makedirs(package_dir)
        except Exception as e:
            logger.error("Could not create directory for packaged models")
            raise e

    try:
        bucket = s3_connect()
        package_folder = s3_models_dir + model_name
        logger.debug(
            "Downloading latest model package from {}".format(package_folder))

        for obj in bucket.objects.filter(Prefix=package_folder):
            filename = obj.key.rpartition("/")[2]
            download_path = "{}/{}".format(package_dir, filename)
            logger.debug("Getting {} to download to {}".format(
                obj.key, download_path))
            bucket.Object(obj.key).download_file(download_path)

    except Exception as e:
        logger.error(
            "Error downloading all model files, removing any local downloads")
        logger.error(e)
        shutil.rmtree(package_dir)
        os.rmdir(package_dir)
        raise OSError("Could not download model files to system")
    return model_name


def download_models(s3_models_dir, local_packaged_models_dir, select="all"):
    """download all models: this gets all models that AREN'T already available
    locally from s3 model repo
    Args:
        s3_models_dir: s3 model directory. i.e. models/v3/
        local_packaged_models_dir: the local directory where models are stored.
    Returns:
        model_name: list - names of pulled down models
    """

    try:
        bucket = s3_connect()
        package_folder = s3_models_dir
        logger.debug(
            "Downloading latest model package from {}".format(package_folder))
        curr_local_models = get_local_model_package_names(
            local_packaged_models_dir)
        model_diff_list = []
        if select == "all":
            s3_models = get_models_list(s3_models_dir)
            s3_models = set([x[0].split("/")[0] for x in s3_models])
            model_diff_list = s3_models - set(curr_local_models)
        else:
            if select in curr_local_models:
                logger.info(f"Model {select} already exists.")
                return model_diff_list
            else:
                model_diff_list = [select]

        for obj in bucket.objects.filter(Prefix=package_folder):
            model_prefix = obj.key.split("/")[2]
            filename = obj.key.split("/")[3]
            if model_prefix in model_diff_list:
                package_dir = "{}/{}".format(
                    local_packaged_models_dir, model_prefix)
                download_path = "{}/{}".format(package_dir, filename)
                bucket = s3_connect()
                logger.debug("Checking  package dir {}".format(package_dir))

                if not os.path.isdir(package_dir):
                    logger.debug("Model package directory does not exist.")
                    try:
                        logger.debug("Attempting to create model package")
                        if not os.path.isdir(package_dir):
                            os.makedirs(package_dir)
                    except Exception as e:
                        logger.error(
                            "Could not create directory for packaged models")
                        raise e
                logger.debug(
                    "Getting {} to download to {}".format(
                        obj.key, download_path)
                )
                bucket.Object(obj.key).download_file(download_path)

    except Exception as e:
        logger.error(
            "Error downloading all model files, removing any local downloads")
        logger.error(e)
        shutil.rmtree(package_dir)
        os.rmdir(package_dir)
        raise OSError("Could not download model files to system")
    return model_diff_list


def get_transformers(model_path="transformers_v4/transformers.tar", overwrite=False):
    bucket = s3_connect()
    models_path = "dataScience/models"
    try:
        if glob.glob(os.path.join(models_path, "transformer*")):
            if not overwrite:
                print(
                    "transformers exists -- not pulling from s3, specify overwrite = True"
                )
                return
        for obj in bucket.objects.filter(Prefix=model_path):
            print(obj)
            bucket.download_file(
                obj.key, os.path.join(models_path, obj.key.split("/")[-1])
            )
            compressed = obj.key.split("/")[-1]
        cache_path = os.path.join(models_path, compressed)
        print("uncompressing: " + cache_path)
        compressed_filename = compressed.split(".tar")[0]
        if os.path.isdir(f"{models_path}/{compressed_filename}"):
            os.rename(
                f"{models_path}/{compressed_filename}",
                f"{models_path}/{compressed_filename}_backup",
            )
        tar = tarfile.open(cache_path)
        tar.extractall(models_path)
        tar.close()
    except Exception:
        print("cannot get transformer model")
        raise


def get_sentence_index(model_path="sent_index/", overwrite=False):
    bucket = s3_connect()
    models_path = "dataScience/models"
    try:
        if glob.glob(os.path.join(models_path, "sent_index*")):
            if not overwrite:
                print(
                    "sent_index exists -- not pulling from s3, specify overwrite = True"
                )
                return
        for obj in bucket.objects.filter(Prefix=model_path):
            print(obj)
            bucket.download_file(
                obj.key, os.path.join(models_path, obj.key.split("/")[-1])
            )
            compressed = obj.key.split("/")[-1]
        cache_path = os.path.join(models_path, compressed)
        print("uncompressing: " + cache_path)
        compressed_filename = compressed.split(".tar")[0]
        if os.path.isdir(f"{models_path}/{compressed_filename}"):
            os.rename(
                f"{models_path}/{compressed_filename}",
                f"{models_path}/{compressed_filename}_backup",
            )
        tar = tarfile.open(cache_path)
        tar.extractall(models_path)
        tar.close()
    except Exception:
        print("cannot get transformer model")
        raise


def get_local_model_package_names(local_packaged_models_dir):
    return list(
        filter(
            lambda x: os.path.isdir(os.path.join(
                local_packaged_models_dir, x)),
            os.listdir(local_packaged_models_dir),
        )
    )


def view_all_datasets():
    bucket = s3_connect()

    prefix = "eval_data/"
    all_datasets = set()
    for obj in bucket.objects.filter(Prefix=prefix):
        object_key = obj.key.replace(prefix, "")
        object_key = object_key.split("/")[:2]
        object_key = "/".join(object_key)
        all_datasets.add(object_key)

    logger.info("Available datasets:")
    for dataset in all_datasets:
        logger.info(f"\t{dataset}")


def store_eval_data(folder_path, version):
    """
    store_eval_data - write eval data to s3 bcuekt
        params: folder_path (str), folder containing data
                version (int), version number of dataset
        output:
    """
    bucket = s3_connect()
    folder_name = os.path.normpath(folder_path)
    folder_name = os.path.basename(folder_name)
    s3_directory = f"eval_data/{folder_name}/v{str(version)}"

    if not os.path.isdir(folder_path):
        logger.debug(folder_path + "does not exist...")
        return None

    try:
        for fname in os.listdir(folder_path):
            fpath = os.path.join(folder_path, fname)
            s3_path = os.path.join(s3_directory, folder_name, fname)
            bucket.Object(s3_path).delete()
            bucket.upload_file(fpath, s3_path)
    except:
        logger.debug(fpath + "failed to store in S3")


def download_eval_data(dataset_name, save_dir, version=None):
    """
    store_eval_data - download eval data to local directory
        params: folder_path (str), folder containing data
                version (int), version number of dataset
        output:
    """
    save_dir = os.path.join(save_dir, dataset_name)
    if not os.path.isdir(save_dir):
        os.mkdir(save_dir)

    bucket = s3_connect()

    prefix = "eval_data/"
    try:
        all_datasets = set()
        for obj in bucket.objects.filter(Prefix=prefix):
            object_key = obj.key.replace(prefix, "")
            dataset = object_key.split("/")[0]
            all_datasets.add(dataset)
    except:
        logger.debug(
            "Failed to query dataset version. Maybe the dataset doesn't exist")

    if dataset_name not in all_datasets:
        logger.debug(f"{dataset_name} not in available datasets.")
        logger.debug(f"Available datasets are {list(all_datasets)}")
        return None

    prefix = f"eval_data/{dataset_name}/"
    try:
        all_versions = set()
        for obj in bucket.objects.filter(Prefix=prefix):
            object_key = obj.key.replace(prefix, "")
            object_ver = int(object_key.split("/")[0][1:])
            all_versions.add(object_ver)
    except:
        logger.debug(
            "Failed to query dataset version. Maybe the dataset doesn't exist")

    if version is None:
        version = max(all_versions)
    elif version not in all_versions:
        logger.debug(f"Version {version} not found.")
        logger.debug(f"Available versions are {list(all_versions)}")
        return None

    logger.info(f"Downloading {dataset_name} version {version}...")
    prefix += f"v{version}"
    try:
        for obj in bucket.objects.filter(Prefix=prefix):
            fname = obj.key.split("/")[-1]
            save_name = os.path.join(save_dir, fname)
            bucket.download_file(obj.key, save_name)
    except:
        logger.debug(f"Failed to download {obj.key}")
