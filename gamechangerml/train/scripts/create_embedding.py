from gamechangerml.src.search.sent_transformer.model import SentenceEncoder
from gamechangerml.src.utilities.arg_parser import LocalParser

from gamechangerml.src.utilities import utils as utils
from gamechangerml.src.utilities import aws_helper as aws_helper
from gamechangerml.api.utils.logger import logger
from datetime import datetime
from distutils.dir_util import copy_tree

import os
import torch
import json
from pathlib import Path
import tarfile
import typing as t
import subprocess
from gamechangerml.train.pipeline import Pipeline


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
    pipeline = Pipeline()
    pipeline.create_embedding(**args.__dict__)


if __name__ == "__main__":
    main()
