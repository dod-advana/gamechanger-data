import logging
from gamechangerml.src.utilities.utils import *
from gamechangerml.src.utilities.arg_parser import LocalParser

logger = logging.getLogger("gamechanger")
"""
if __name__ == "__main__":
    log_fmt = (
        "[%(asctime)s %(levelname)-8s], [%(filename)s:%(lineno)s - "
        + "%(funcName)s()], %(message)s"
    )
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    parser = LocalParser("Builds all support models for query expansion")
    parser.add_argument(
        "-d",
        "--dataset-name",
        dest="dataset_name",
        required=False,
        default=None,
        type=str,
        help="dataset name to download",
    )
    parser.add_argument(
        "-c",
        "--corpus-dir",
        dest="corpus_dir",
        required=False,
        default=None,
        type=str,
        help="directory for saving the evaluation corpus",
    )
    parser.add_argument(
        "-v",
        "--version",
        dest="version",
        required=False,
        default=None,
        type=int,
        help="version number of dataset; default=None (get latest version)",
    )
    parser.add_argument(
        "-l",
        "--l",
        dest="list_datasets",
        required=False,
        default=True,
        type=bool,
        help="boolean to check if the user wants to look at available datasets",
    )

    args = parser.parse_args()

    if args.list_datasets:
        view_all_datasets()

    if args.dataset_name is None:
        pass
    elif args.corpus_dir is None:
        logger.debug("Corpus directory is not set.")
    else:
        download_eval_data(args.dataset_name, args.corpus_dir, args.version)
"""

if __name__ == "__main__":
    log_fmt = (
        "[%(asctime)s %(levelname)-8s], [%(filename)s:%(lineno)s - "
        + "%(funcName)s()], %(message)s"
    )
    logging.basicConfig(level=logging.INFO, format=log_fmt)
    view_all_datasets()
    print("")
    dataset = input("Which dataset do you want (only type the name)?\t")
    print("")
    save_dir = input(f"Where should the dataset be saved?\t\t")
    print("")
    logger.info(f"Downloading [{dataset}]...")
    
    if not any([a == "" for a in [dataset, save_dir]]):
        download_eval_data(dataset, save_dir)
