"""
usage: entity_extraction_example.py [-h] -m {spacy,hf} [-c CORPUS_DIR]

Example Named Entity Extraction (NER)

optional arguments:
  -h, --help            show this help message and exit
  -m {spacy,hf}, --method {spacy,hf}
  -c CORPUS_DIR, --corpus-dir CORPUS_DIR
                        corpus directory

"""
import logging
import os
import re
from collections import defaultdict
from pathlib import Path
from pprint import pformat

from gamechangerml.src.featurization.ner import NER
from gamechangerml.src.utilities.arg_parser import LocalParser
from gamechangerml.src.utilities.timer import Timer

logger = logging.getLogger(__name__)

re_list = list()
re_list.append(re.compile("^##\\S+"))
re_list.append(re.compile("^(?:title|section|chapter)\\s?\\d+?$", re.I))


def _num_words(entity):
    return entity.count(" ")


def _keep_entity(entity):
    if _num_words(entity.strip()):
        for regex in re_list:
            match_obj = re.search(regex, entity)
            if match_obj is not None:
                return False
        return True
    return False


def _spacy_extract(corpus_dir, ner, entity_dict):
    with Timer():
        logger.info("finding entities using spaCy NER")
        for lbl, ent, file_name, doc_id in ner.extract(corpus_dir):
            if _keep_entity(ent):
                k = "~".join((lbl, doc_id))
                entity_dict[k].add(ent)


def _hf_extract(corpus_dir, ner, entity_dict):
    with Timer():
        logger.info("finding entities with HF NER")
        for lbl, ent, file_name, doc_id in ner.extract(corpus_dir):
            if _keep_entity(ent):
                k = "~".join((lbl, doc_id))
                entity_dict[k].add(ent)


def main(method, corpus_dir):
    ner = None
    if method == "hf":
        ner = NER(model_type="hf-transformer", entity_types=["I-ORG", "B-ORG"])
    elif method == "spacy":
        ner = NER(model_type="spacy-large", entity_types=["ORG", "LAW"])

    entity_dict = defaultdict(set)
    if method == "spacy":
        _spacy_extract(corpus_dir, ner, entity_dict)
    else:
        _hf_extract(corpus_dir, ner, entity_dict)

    for k in sorted(entity_dict.keys()):
        lbl, doc_id = k.split("~")
        logger.info("{}: {}".format(lbl, doc_id))
        entity_list = sorted(list(entity_dict[k]))
        logger.info(pformat(entity_list))


if __name__ == "__main__":
    import sys

    log_fmt = (
        "[%(asctime)s %(levelname)-8s], [%(filename)s:%(lineno)s - "
        + "%(funcName)s()], %(message)s"
    )
    logging.basicConfig(level=logging.DEBUG, format=log_fmt)

    here = os.path.dirname(os.path.abspath(__file__))
    p = Path(here)

    c_dir = os.path.join(p.parent, "data", "test_data")

    parser = LocalParser(description="Example Named Entity Extraction (NER)")
    parser.add_argument(
        "-m",
        "--method",
        choices=["spacy", "hf"],
        dest="method",
        type=str,
        required=True,
        default="spacy",
    )
    parser.add_argument(
        "-c",
        "--corpus-dir",
        dest="corpus_dir",
        type=str,
        default=c_dir,
        help="corpus directory",
    )

    args = parser.parse_args()
    sys.exit(main(args.method, c_dir))
