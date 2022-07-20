"""
usage: python build_qe_model.py [-h] -c CORPUS_DIR -i INDEX_DIR [-t NUM_TREES]
                                [-k NUM_KEYWORDS] [-w WEIGHT_FILE] -g NGRAM
                                [-a ABBRV_FILE] [-m]

optional arguments:
  -h, --help            show this help message and exit
  -c CORPUS_DIR, --corpus-dir CORPUS_DIR
                        directory of document corpus; default=Config.DATA_DIR
  -i INDEX_DIR, --index-dir INDEX_DIR
                        directory for saving the index;
                        default=Config.MODEL_DIR
  -t NUM_TREES, --num-trees NUM_TREES
                        number of trees in the index; default=125
  -k NUM_KEYWORDS, --num-keywords NUM_KEYWORDS
                        number of keywords per page to add to the index,
                        default=3
  -w WEIGHT_FILE, --word-wt WEIGHT_FILE
                        path + name of the word weight file in aux_data/
  -g NGRAM, --ngram NGRAM
                        tuple of (min, max) length of keywords to find
  -a ABBRV_FILE, --abbrv-file ABBRV_FILE
                        path and file for the short-form to long-form
                        abbreviation mapping
  -m, --merge-word-sim  Whether or not the word sim (wiki-news-300d-1M.vec)
                        results should be concatenated to the annoy index
"""
import logging
import os
import pickle
import time

from annoy import AnnoyIndex

import gamechangerml.src.search.query_expansion.build_ann_cli.version_ as v
from gamechangerml.src.featurization.keywords.rake import Rake
from gamechangerml.src.search.query_expansion.sif_alg import sif_embedding
from gamechangerml.src.search.query_expansion.utils import QEConfig
from gamechangerml.configs.config import QexpConfig
from gamechangerml.src.search.query_expansion.word_wt import get_word_weight
from gamechangerml.src.utilities.np_utils import is_zero_vector
from gamechangerml.src.utilities.spacy_model import (
    get_lg_vectors,
    spacy_vector_width,
)
from gamechangerml.src.utilities.text_generators import gen_json, child_doc_gen
from gamechangerml.src.utilities.text_utils import simple_clean
from gamechangerml.src.utilities.timer import Timer

from gamechangerml import DATA_PATH, MODEL_PATH
FEATURES_DATA_PATH = os.path.join(DATA_PATH, "features")
logger = logging.getLogger(__name__)

empty_dict = dict()
cfg = QEConfig()
index_prefix, index_ext, vocab_prefix, vocab_ext = cfg.index_attribs


def build_ann_index(nlp, dict_to_index, ann_index=None):
    vector_dim = spacy_vector_width(nlp)
    if ann_index is None:
        ann_index = AnnoyIndex(vector_dim, cfg.embedding_dist)
        logger.info("new index created")

    idx = 0
    for text, vec in dict_to_index.items():
        ann_index.add_item(idx, vec)
        idx += 1
    return dict_to_index.keys(), ann_index


def build_kws(text, kw_alg, nlp, word_wt, num_kws, ngram):
    if not text.strip():
        return empty_dict

    kw_dict = dict()
    keywords = kw_alg.rank(text, ngram=ngram, topn=num_kws, clean=False)
    for kw in keywords:
        vec = sif_embedding(kw, nlp, word_wt, strict=True)
        if is_zero_vector(vec):
            return empty_dict
        else:
            kw_dict[kw] = vec
    return kw_dict


def save_index(ann_index, vocab_map, output_dir):
    ts = str(time.time())
    idx_name = os.path.join(output_dir, index_prefix + ts + index_ext)
    vocab_name = os.path.join(output_dir, vocab_prefix + ts + vocab_ext)
    try:
        ann_index.save(idx_name)
        logger.info("index saved to {}".format(idx_name))
        with open(vocab_name, "wb") as fh:
            pickle.dump(vocab_map, fh)
        logger.info("vocabulary map saved to {}".format(vocab_name))
    except IOError as e:
        logger.exception("{}: {}".format(type(e), str(e)), exc_info=True)
        raise


def main(
    corpus_dir,
    index_dir,
    num_trees=125,
    num_keywords=2,
    ngram=(1, 3),
    weight_file=None,
    abbrv_file=None,
    merge_word_sim=False
):
    """
    `main` corresponding to the command line to build the approximate
    nearest neighbor search index.

    Args:
        corpus_dir (str): Path where the `.json` corpus files reside

        index_dir (str): Path where the resulting indexes will be stored

        num_trees (int): Number of search trees for the index; default = 125

        num_keywords (int): Number of keywords per corpus page; default = 3

        ngram (tuple): minimum and maximum length of a key-phrase;
            default = (1, 2)

        word_wt_file (str|None): Directory holding the word wt file named
            `enwiki_vocab_min200.txt`; default=None

        abbrv_file (str|None): path and file name holding the dictionary of
            short-form to long forms of abbreviations; default=None

    Raises:
        FileNotFoundError if any required file cannot be read or a required
            directory does not exist
    """
    logger.info("{} version {}".format(__name__, v.__version__))
    if not os.path.isdir(index_dir):
        raise FileNotFoundError(
            "directory not found; got {}".format(str(index_dir))
        )
    if not os.path.isdir(corpus_dir):
        raise FileNotFoundError(
            "directory not found; got {}".format(str(corpus_dir))
        )

    if weight_file is None:
        weight_file = os.path.join(FEATURES_DATA_PATH, "enwiki_vocab_min200.txt")
    word_wt = get_word_weight(weight_file=weight_file, a=1e-03)

    if ngram[0] < 1:
        raise ValueError("minimum ngram must be > 0; got {}".format(ngram))

    logger.info("loading spaCy vectors")
    nlp = get_lg_vectors()

    # TODO add title and abbreviation embeddings

    kw_alg = Rake(stop_words="smart")
    vec_dict = dict()
    empty_text = 0
    rejected = 0

    with Timer():
        p_count = 0
        doc_gen = gen_json(corpus_dir, key="pages")
        for text, f_name in child_doc_gen(doc_gen):
            if not text.strip():
                empty_text += 1
                continue
            text = simple_clean(text)

            kw_vectors = build_kws(
                text, kw_alg, nlp, word_wt, num_keywords, ngram
            )
            if kw_vectors:
                vec_dict.update(kw_vectors)
            else:
                rejected += 1

            if p_count in [1, 5, 25, 100, 500] or p_count % 1000 == 0:
                logger.info(
                    "pages processed {:>7,d}   num keywords : {:>7,d}".format(
                        p_count, len(vec_dict)
                    )
                )
            p_count += 1

        logger.info("          empty texts : {:9,d}".format(empty_text))
        logger.info("rejected out-of-vocab : {:9,d}".format(rejected))
        logger.info("total pages processed : {:9,d}".format(p_count))
        logger.info("       items to index : {:9,d}".format(len(vec_dict)))
        vocab_map, ann_index = build_ann_index(nlp, vec_dict)
        vocab_map = list(vocab_map)
        ## Merge in word similarity vocab/vectors to ann index
        if merge_word_sim:
            try:
                from gamechangerml.src.featurization.word_sim import WordSim
                word_sim = WordSim(os.path.join(MODEL_PATH,"transformers","wiki-news-300d-1M.bin"))
                word_sim_text_vec_dict = dict(zip(word_sim.model.index_to_key,
                                                word_sim.model.vectors))
                logger.info(f"Attempting to add in {len(word_sim.model.index_to_key)} total vocab/vectors from the "
                            f"word similarity model")
                current_idx = len(vocab_map)
                for text, vec in word_sim_text_vec_dict.items():
                    ann_index.add_item(current_idx, vec)
                    vocab_map.append(text)
                    current_idx+=1
                logger.info("Successfully added in word similarity results to ann index")
            except Exception as e:
                logger.error(f"Exception thrown when attempting to merge in word similarity results: {e}, saving ANNOY "
                             f"index without word similarity included")

        with Timer():
            logger.info("building index...")
            ann_index.build(num_trees)

    save_index(ann_index, vocab_map, index_dir)


if __name__ == "__main__":
    """
    Command line for building the approximate nearest neighbor index. See
    the __docstring__ for usage or use `--help`.
    """
    from gamechangerml.src.utilities.arg_parser import LocalParser

    log_fmt = (
        "[%(asctime)s %(levelname)-8s], [%(filename)s:%(lineno)s - "
        + "%(funcName)s()], %(message)s"
    )
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    parser = LocalParser("python build_qe_model.py")
    parser.add_argument(
        "-c",
        "--corpus-dir",
        dest="corpus_dir",
        required=True,
        type=str,
        help="directory of document corpus; default=Config.DATA_DIR",
    )
    parser.add_argument(
        "-i",
        "--index-dir",
        dest="index_dir",
        required=True,
        type=str,
        help="directory for saving the index; default=Config.MODEL_DIR",
    )
    parser.add_argument(
        "-t",
        "--num-trees",
        dest="num_trees",
        required=False,
        default=125,
        type=int,
        help="number of trees in the index; default=125",
    )
    parser.add_argument(
        "-k",
        "--num-keywords",
        dest="num_keywords",
        required=False,
        default=3,
        type=int,
        help="number of keywords per page to add to the index, default=3",
    )
    parser.add_argument(
        "-w",
        "--word-wt",
        dest="weight_file",
        required=False,
        help="path + name of the word weight file in aux_data/",
    )
    parser.add_argument(
        "-g",
        "--ngram",
        dest="ngram",
        required=True,
        help="tuple of (min, max) length of keywords to find",
    )
    parser.add_argument(
        "-a",
        "--abbrv-file",
        dest="abbrv_file",
        required=False,  # TODO change to True once this is integrated
        help="path and file for the short-form to long-form abbreviation mapping",  # noqa
    )
    parser.add_argument(
        "-m",
        "--merge-word-sim",
        dest="merge_word_sim",
        action = 'store_true',
        help="Whether or not the word sim (wiki-news-300d-1M.vec) results should be concatenated to the annoy index"
    )
    args = parser.parse_args()
    if isinstance(args.ngram[0], str):
        ngram = args.ngram.replace("(", "").replace(")", "").split(",")
        ngram = (int(ngram[0]), int(ngram[1]))
    else:
        ngram = args.ngram
    if int(ngram[0]) - int(ngram[1]) > 0:
        raise ValueError("invalid argument ngram; got {}".format(args.ngram))

    logger.info("Building query expansion embedding index")
    with Timer():
        main(
            args.corpus_dir,
            args.index_dir,
            int(args.num_trees),
            int(args.num_keywords),
            ngram,
            args.weight_file,
            args.abbrv_file,
            args.merge_word_sim
        )
    logger.info("complete")
