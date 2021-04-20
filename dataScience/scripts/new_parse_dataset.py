from dataScience.src.featurization.doc_parser.parser import DocumentParser
from dataScience.src.utilities.arg_parser import LocalParser

import os
import json
import logging
from pathlib import Path

from tqdm import tqdm

def main(corpus_dir, output_dir):
    metadata = {}
    mapping = {}
    for fname in tqdm(os.listdir(corpus_dir)):
        if not fname.endswith(".json"):
            continue
        if not fname.lower().startswith("dod"):
            continue
        
        doc_parser = DocumentParser()
        doc_parser.parse(os.path.join(corpus_dir, fname))
        doc_parser.save_dict(os.path.join(output_dir, fname))

        for key, value in doc_parser.mapper:
            mapping[key] = value

        metadata[fname] = doc_parser.title

    with open(os.path.join(output_dir, "metadata.json"), "w") as fp:
        json.dump(metadata, fp)


if __name__ == "__main__":
    log_fmt = (
        "[%(asctime)s %(levelname)-8s], [%(filename)s:%(lineno)s - "
        + "%(funcName)s()], %(message)s"
    )
    logging.basicConfig(level=logging.DEBUG, format=log_fmt)

    here = os.path.dirname(os.path.abspath(__file__))
    p = str(Path(here))
    p = p.split("/")[:-3]
    p = "/".join(p)

    c_dir = os.path.join(p, "corpus", "corpus_20210203")
    o_dir = os.path.join(p, "corpus", "new_dod_parse")

    parser = LocalParser(description="Document Parsing")
    parser.add_argument(
        "-c",
        "--corpus-dir",
        dest="corpus_dir",
        type=str,
        required=False,
        default=c_dir,
        help="Directory containing GC format dataset"
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        dest="output_dir",
        type=str,
        required=False,
        default=o_dir,
        help="Output directory for parsed data"
    )

    args = parser.parse_args()
    main(
        args.corpus_dir,
        args.output_dir
    )
