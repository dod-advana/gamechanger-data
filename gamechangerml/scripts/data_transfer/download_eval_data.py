"""Script to download evaluation data. Requires command-line input."""

from gamechangerml.src.services import S3Service
from gamechangerml.configs import S3Config
from gamechangerml.src.data_transfer import download_eval_data
from gamechangerml.src.utilities import configure_logger


if __name__ == "__main__":
    logger = configure_logger()
    bucket = S3Service.connect_to_bucket(S3Config.BUCKET_NAME, logger)
    available_datasets = [
        "/".join(x.split("/")[2:])
        for x in
        S3Service.get_object_names(bucket, S3Config.EVAL_DATA_DIR, "path")
    ]
    logger.info(f"Available datasets are: {available_datasets}.")

    # Prompt the user to enter the dataset name and where to save it.
    dataset = input("Which dataset do you want?\n")
    save_dir = input("Where should the dataset be saved?\n")
    logger.info(f"Downloading [{dataset}]...")
    
    if not any([x == "" for x in [dataset, save_dir]]):
        download_eval_data(dataset, save_dir)
