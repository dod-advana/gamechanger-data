from dataScience.src.search.sent_transformer.model import SentenceEncoder
from dataScience.src.utilities.arg_parser import LocalParser

from dataScience.src.utilities import utils as utils
from dataScience.src.utilities import aws_helper as aws_helper

from datetime import datetime
from distutils.dir_util import copy_tree

import os
import torch
import json
from pathlib import Path

import typing as t
import subprocess
import logging

logger = logging.getLogger()


def create_tgz_from_dir(
    src_dir: t.Union[str, Path],
    dst_archive: t.Union[str, Path],
    exclude_junk: bool = False,
) -> None:
    src_dir = Path(src_dir).resolve()
    dst_archive = Path(dst_archive).resolve()
    exclude_junk_args = ["--exclude", "*/.git/*", "--exclude", "*/.DS_Store/*"]
    subprocess.run(
        args=[
            "tar",
            "-czf",
            str(dst_archive),
            "-C",
            str(src_dir),
            *(exclude_junk_args if exclude_junk else []),
            ".",
        ],
        check=True,
    )


def main():
    parser = LocalParser()
    parser.add_argument(
        "-c",
        "--corpus",
        dest="corpus",
        required=True,
        type=str,
        help="Folder path containing GC Corpus",
    )
    parser.add_argument(
        "-e",
        "--existing-embeds",
        dest="existing_embeds",
        required=False,
        default=None,
        type=str,
        help="Folder path containing existing embeddings",
    )
    parser.add_argument(
        "-em",
        "--encoder-model",
        dest="encoder_model",
        required=False,
        default="msmarco-distilbert-base-v2",
        type=str,
        help="Encoder model used to encode the dataset",
    )
    parser.add_argument(
        "-g",
        "--gpu",
        dest="gpu",
        required=False,
        default=True,
        type=bool,
        help="Boolean check if encoder model will be loaded to the GPU",
    )
    parser.add_argument(
        "-u",
        "--upload",
        dest="upload",
        required=False,
        default=False,
        type=bool,
        help="Boolean check if file will be uploaded to S3",
    )
    parser.add_argument(
        "-v",
        "--version",
        dest="version",
        required=False,
        default="v4",
        type=str,
        help="version string, must start with v, i.e. v1",
    )
    args = parser.parse_args()

    # Error fix for saving index and model to tgz
    # https://github.com/huggingface/transformers/issues/5486
    os.environ["TOKENIZERS_PARALLELISM"] = "false"

    # GPU check
    use_gpu = args.gpu
    if use_gpu and not torch.cuda.is_available:
        print("GPU is not available. Setting `gpu` argument to False")
        use_gpu = False

    # Define model saving directories
    # here = os.path.dirname(os.path.realpath(__file__))
    # p = Path(here)
    model_dir = os.path.join("dataScience", "models")
    encoder_path = os.path.join(model_dir, "transformers", args.encoder_model)

    index_name = datetime.now().strftime("%Y%m%d")
    local_sent_index_dir = os.path.join(model_dir, "sent_index_" + index_name)

    # Define new index directory
    if not os.path.isdir(local_sent_index_dir):
        os.mkdir(local_sent_index_dir)

    # If existing index exists, copy content from reference index
    if args.existing_embeds is not None:
        copy_tree(args.existing_embeds, local_sent_index_dir)

    logger.info("Loading Encoder Model...")
    encoder = SentenceEncoder(encoder_path, use_gpu)
    logger.info("Creating Document Embeddings...")
    encoder.index_documents(args.corpus, local_sent_index_dir)

    # Generating process metadata
    metadata = {
        "user": str(os.getlogin()),
        "date_created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "doc_id_count": len(encoder.embedder.config["ids"]),
        "corpus_name": args.corpus,
        "encoder_model": args.encoder_model,
    }

    # Create metadata file
    metadata_path = os.path.join(local_sent_index_dir, "metadata.json")
    with open(metadata_path, "w") as fp:
        json.dump(metadata, fp)

    # Create .tgz file
    dst_path = local_sent_index_dir + ".tar.gz"
    create_tgz_from_dir(src_dir=local_sent_index_dir, dst_archive=dst_path)

    # Upload to S3
    if args.upload:
        # Loop through each file and upload to S3
        s3_sent_index_dir = f"gamechanger/models/sentence_index/{args.version}"
        logger.info(f"Uploading files to {s3_sent_index_dir}")
        logger.info(f"\tUploading: {local_sent_index_dir}")
        local_path = os.path.join(dst_path)
        s3_path = os.path.join(
            s3_sent_index_dir, "sent_index_" + index_name + ".tar.gz"
        )
        utils.upload_file(local_path, s3_path)


if __name__ == "__main__":
    main()
