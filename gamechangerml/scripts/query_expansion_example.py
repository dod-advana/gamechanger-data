"""
usage: query_expansion_example.py [-h] -i INDEX_DIR -q QUERY_FILE

python query_expansion_example.py

optional arguments:
  -h, --help            show this help message and exit
  -i INDEX_DIR, --index-dir INDEX_DIR
                        ANN index directory
  -q QUERY_FILE, --query-file QUERY_FILE
                        text file containing one sample query per line
"""
import logging
import os.path
import sys

from gamechangerml.src.search.query_expansion.qe import QE
from gamechangerml.src.utilities.spacy_model import get_lg_vectors
from gamechangerml.src.utilities.np_utils import is_zero_vector

from gamechangerml.src.utilities.arg_parser import LocalParser
from gamechangerml.src.utilities.text_utils import simple_clean
from gamechangerml.src.utilities.timer import Timer

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    log_fmt = (
        "[%(asctime)s %(levelname)-8s], [%(filename)s:%(lineno)s - "
        + "%(funcName)s()], %(message)s"
    )
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    parser = LocalParser(description="python query_expansion_example.py")
    parser.add_argument(
        "-i",
        "--index-dir",
        dest="index_dir",
        required=True,
        type=str,
        help="ANN index directory",
    )
    parser.add_argument(
        "-q",
        "--query-file",
        dest="query_file",
        required=True,
        type=str,
        help="text file containing one sample query per line",
    )
    args = parser.parse_args()

    if not os.path.isdir(args.index_dir):
        logger.fatal("{} is not a directory".format(args.model_dir))
        logger.fatal("You may need to first build the search index")
        logger.fatal("See the README in the query_expansion directory")
        logger.fatal("for details.")
        sys.exit(2)

    logger.info("loading spaCy")
    nlp = get_lg_vectors()

    with open(args.query_file, "r") as fh:
        sample_queries = [simple_clean(q.replace('"', "")) for q in fh]

    logger.info("trying {:,} queries".format(len(sample_queries)))
    logger.info("creating object")
    try:
        with Timer():
            qe_ = QE(
                args.index_dir,
                method="emb",
                vocab_file="word-freq-corpus-20201101.txt",
            )
            logger.debug("index loaded")
    except FileNotFoundError as e:
        logger.fatal("{}: {}".format(type(e), str(e)), exc_info=True)
        raise

    z_vec_errors = 0
    no_expansion = 0
    for q_str in sample_queries:
        expanded_ = qe_.expand(q_str, topn=2)
        if not expanded_:
            no_expansion += 1
        for ex_term in expanded_:
            chk = [is_zero_vector(token.vector) for token in nlp(ex_term)]
            if True in chk:
                logger.error("{} zero vector in {}".format(q_str, ex_term))
                z_vec_errors += 1
            else:
                logger.info("{:>45s} -> {}".format(q_str, expanded_))

    logger.info("-" * 80)
    logger.info(
        " num OOV expansion terms out of {:5,d} examples : {:>5,d}".format(
            len(sample_queries), z_vec_errors
        )
    )
    logger.info(
        "               query strings with no expansion : {:>5,d}".format(
            no_expansion)
    )
