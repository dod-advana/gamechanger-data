import os
import json
import logging

from collections import defaultdict

import pandas as pd
from fuzzywuzzy import fuzz

from gamechangerml.src.utilities.arg_parser import LocalParser

logger = logging.getLogger("gamechanger")

# List of common text that needed to be substituted to improve
# matching. All "old_text":"new_text" pairs must be in lowercase
SUBSTITUTE_DICTIONARY = {" issuance": "i"}

def preprocess_text(text):
    """
    Preprocess text before being passed to
    the fuzzy matching

    Args:
        text (string): Text to be processed

    Returns:
        new_text (string): Processed text
    """
    new_text = text.lower()
    for old_str, new_str in SUBSTITUTE_DICTIONARY.items():
        new_text = new_text.replace(old_str, new_str)
    return new_text

def retrieve_document_list(corpus_dir):
    """
    Retrieve the list of documents from
    the filename of each file in a corpus directory

    Args:
        corpus_dir (string): Directory containing all
                             document files

    Returns:
        document_list (list): List of document names 
    """
    document_list = []
    for fpath in os.listdir(corpus_dir):
        fpath = fpath.replace(".json", "").split(',')[0]
        document_list.append(fpath)
    document_list = sorted(document_list)
    return document_list

def get_top_n(document, list_documents, k = 5):
    """
    Get the top n documents from the list_documents 
    with the highest Levenshtein similarity score 
    with the input document name

    Args:
        document (string): Directory containing all
                             document files

    Returns:
        document_list (list): List of document names 
    """
    order_df = pd.DataFrame(columns = ["Valid Document Name", "Score"])
    processed_doc = preprocess_text(document)

    for valid_doc_name in list_documents:
        score = fuzz.partial_ratio(processed_doc, preprocess_text(valid_doc_name))
        order_df.loc[len(order_df)] = [valid_doc_name, score]
    order_df.sort_values(by="Score", ascending = False, inplace = True)
    return order_df.head(k).reset_index()

def main(query_dir, corpus_dir, output_file):
    search_pairs = pd.read_csv(query_dir)
    document_list = retrieve_document_list(corpus_dir)

    working_pairs = defaultdict(list)

    for idx, (query, document) in search_pairs.iterrows():
        if document not in document_list:
            order_df = get_top_n(document, document_list, k=5)
            logging.info("="*30)
            logging.info(f"[{document}] did not match any of the corpus data. Refer to most likely similar documents below:")
            logging.info(order_df)
            logging.info("="*30)
        else:
            working_pairs[query].append(document)

    if output_file is not None:
        if len(working_pairs) > 0:
            logging.info(f"Saving matched documents to {output_file}")
            with open(output_file, "w") as fp:
                json.dump(dict(working_pairs), fp)
        else:
            logging.info("No documents matching documents in corpus. Please refer to suggested titles above...")

if __name__ == "__main__":
    log_fmt = (
        "[%(asctime)s %(levelname)-8s], [%(filename)s:%(lineno)s - "
        + "%(funcName)s()], %(message)s"
    )
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    parser = LocalParser("Create a GAMECHANGER Gold Standard Dataset")
    parser.add_argument(
        "-q",
        "--query-dir",
        dest="query_dir",
        required=True,
        default=None,
        type=str,
        help="csv file containing the query document files",
    )
    parser.add_argument(
        "-c",
        "--corpus-dir",
        dest="corpus_dir",
        required=True,
        type=str,
        help="directory containing GAMECHANGER corpus",
    )
    parser.add_argument(
        "-o",
        "--output-file",
        dest="output_file",
        required=False,
        default=None,
        type=str,
        help="json file output directory for ground truth data",
    )
    args = parser.parse_args()
    main(args.query_dir,
         args.corpus_dir,
         args.output_file)