"""Utility functions for downloading objects from S3. 

Also see gamechangerml.src.services.s3_service.py
"""

from threading import current_thread
from os import makedirs
from os.path import join, exists, basename

from gamechangerml.src.services.s3_service import S3Service
from gamechangerml.src.utilities import configure_logger
from gamechangerml.configs import S3Config
from gamechangerml.api.utils import processmanager
from gamechangerml.src.data_transfer import delete_local_corpus


def download_corpus_s3(
    s3_corpus_dir,
    output_dir="corpus",
    bucket=None,
    logger=None,
    rm_existing=True,
):
    """Download the corpus from S3.

    Args:
        s3_corpus_dir (str): Path to S3 directory that contains the corpus.
        output_dir (str, optional): Path to directory to download files to.
            Defaults to "corpus".
        bucket (boto3.resources.factory.s3.Bucket or None, optional): Bucket to
            download from. If None, uses S3Service.connect_to_bucket(). Default
            is None.
        logger (logging.Logger or None, optional): If None, uses
            configure_logger(). Default is None.
        rm_existing (bool, optional): True to delete existing files in the
            output directory before downloading, False otherwise. Default is
            True.

    Returns:
        list of str: Paths (in S3) to downloaded files.
    """
    if logger is None:
        logger = configure_logger()

    if bucket is None:
        bucket = S3Service.connect_to_bucket(S3Config.BUCKET_NAME, logger)

    if rm_existing:
        success = delete_local_corpus(output_dir, logger)
        if not success:
            return []

    corpus = []
    process = processmanager.corpus_download

    try:
        filter = bucket.objects.filter(Prefix=f"{s3_corpus_dir}/")
        total = len(list(filter))
        num_completed = 0

        # Initialize Progress
        processmanager.update_status(
            process, num_completed, total, thread_id=current_thread().ident
        )

        logger.info("Downloading corpus from " + s3_corpus_dir)
        for obj in filter:
            corpus.append(obj.key)
            filename = basename(obj.key)
            local_path = join(output_dir, filename)
            # Only grab file if it is not already downloaded
            if ".json" in filename and not exists(local_path):
                bucket.Object(obj.key).download_file(local_path)
                num_completed += 1
            # Update Progress
            processmanager.update_status(
                process,
                num_completed,
                total,
                thread_id=current_thread().ident,
            )
    except Exception:
        logger.exception("Failed to download corpus from S3.")
        processmanager.update_status(
            process, failed=True, thread_id=current_thread().ident
        )

    return corpus

def download_eval_data(
    bucket,
    dataset_name,
    save_dir,
    logger,
    version=None,
    ):
    """Download evaluation data from S3.

    Args:
        bucket (boto3.resources.factory.s3.Bucket): Bucket to download data from.
        dataset_name (str): Name of the dataset to download.
        save_dir (str): Path to local directory to save data.
        logger (logging.Logger)
        version (int or None, optional): Version number of the dataset to 
            download. If None, downloads the latest version. Default is None.

    Returns:
        None
    """
    save_dir = join(save_dir, dataset_name)
    makedirs(save_dir, exist_ok=True)
    
    # Ensure the dataset name exists
    prefix = S3Config.EVAL_DATA_DIR
    all_datasets = S3Service.get_object_names(bucket, prefix, "dir")
    if dataset_name not in all_datasets:
        logger.warning(
            f"{dataset_name} does not exist. Available datasets are: {all_datasets}."
        )
        return None
    
    # Get version numbers available for the given dataset name
    prefix = f"{prefix}{dataset_name}/"
    try:
        all_versions = [
            int(x[1:]) for x in S3Service.get_object_names(bucket, prefix, "dir")
        ]
    except Exception as e:
        logger.exception(f"Error occurred when getting eval data versions: {e}.")
        raise e

    if not all_versions:
        logger.warning("No versions found, nothing to download.")
        return

    # If no version arg provided, get the latest version.
    if version is None:
        version = max(all_versions)
    # If a version arg was provided, verify that the requested version exists
    elif version not in all_versions:
        logger.warning(
            f"Version {version} does not exist. Available versions are: "
            f"{all_versions}"
        )
        return None

    logger.info(f"Downloading {dataset_name} version {version}...")
    S3Service.download(bucket, prefix + f"v{version}", save_dir, logger)

