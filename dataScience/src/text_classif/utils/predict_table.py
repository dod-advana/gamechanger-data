"""
usage: python predict_table.py [-h] -m MODEL_PATH -d DATA_PATH [-b BATCH_SIZE]
                              [-l MAX_SEQ_LEN] -g GLOB [-o OUTPUT_CSV]

Binary classification of each sentence in the files matching the 'glob' in
data_path

optional arguments:
  -h, --help            show this help message and exit
  -m MODEL_PATH, --model-path MODEL_PATH
                        directory of the torch model
  -d DATA_PATH, --data-path DATA_PATH
                        path holding the .json corpus files
  -b BATCH_SIZE, --batch-size BATCH_SIZE
                        batch size for the data samples; default=8
  -l MAX_SEQ_LEN, --max-seq-len MAX_SEQ_LEN
                        maximum sequence length, 128 to 512; default=128
  -g GLOB, --glob GLOB  file glob pattern
  -o OUTPUT_CSV, --output-csv OUTPUT_CSV
                        the .csv for output
"""
import logging
import time
import spacy
import pandas as pd
from argparse import ArgumentParser

import dataScience.src.text_classif.utils.classifier_utils as cu
from dataScience.src.text_classif.utils.entity_coref import EntityCoref
from dataScience.src.text_classif.utils.log_init import initialize_logger
from dataScience.src.text_classif.examples.output_utils import get_agency
from dataScience.src.featurization.abbreviations_utils import get_references, check_duplicates, get_agencies_dict, get_agencies
# from dataScience.src.featurization.extract_improvement.extract_utils import \
#     extract_entities, create_list_from_dict, remove_articles, match_parenthesis

logger = logging.getLogger(__name__)

spacy_model_ = spacy.load('en_core_web_lg')

if __name__ == "__main__":

    desc = "Binary classification of each sentence in the files "
    desc += "matching the 'glob' in data_path"
    parser = ArgumentParser(prog="python predict_table.py", description=desc)
    parser.add_argument(
        "-m",
        "--model-path",
        dest="model_path",
        type=str,
        required=True,
        help="directory of the torch model",
    )
    parser.add_argument(
        "-d",
        "--data-path",
        dest="data_path",
        type=str,
        required=True,
        help="path holding the .json corpus files",
    )
    parser.add_argument(
        "-b",
        "--batch-size",
        dest="batch_size",
        type=int,
        default=8,
        help="batch size for the data samples; default=8",
    )
    parser.add_argument(
        "-l",
        "--max-seq-len",
        dest="max_seq_len",
        type=int,
        default=128,
        help="maximum sequence length, 128 to 512; default=128",
    )
    parser.add_argument(
        "-g",
        "--glob",
        dest="glob",
        type=str,
        required=True,
        help="file glob pattern",
    )
    parser.add_argument(
        "-o",
        "--output-csv",
        dest="output_csv",
        type=str,
        default=None,
        help="the .csv for output",
    )
    parser.add_argument(
        "-a",
        "--agencies-path",
        dest="agencies_path",
        type=str,
        default=None,
        help="the .csv for agency abbreviations",
    )

    initialize_logger(to_file=False, log_name="none")

    args = parser.parse_args()

    df = pd.DataFrame(columns=['entity', 'top_class', 'prob', 'src', 'label', 'sentence'])
    duplicates, aliases = get_agencies_dict(args.agencies_path)

    start = time.time()
    entity_coref = EntityCoref()
    _ = entity_coref.make_table(
        args.model_path,
        args.data_path,
        args.glob,
        args.max_seq_len,
        args.batch_size,
        # args.output_csv,
        output_csv=None
    )

    df = df.append(entity_coref.to_df())
    df = df[df.top_class == 1].reset_index()

    df['agencies'] = get_agencies(file_dataframe=df, 
             doc_dups=None, 
             duplicates=duplicates, 
             agencies_dict=aliases)
    df = get_agency(df, spacy_model_)
    df['refs'] = get_references(df, doc_title_col='src')

    rename_dict = {
        'entity': 'Organization / Personnel',
        'sentence': 'Responsibility Text',
        'agencies': 'Other Organization(s) / Personnel Mentioned',
        'refs': 'Documents Referenced',
        'title': 'Document Title',
        'source': 'Source Document'
    }
    renamed_df = df.rename(columns=rename_dict)
    final_df = renamed_df[['Source Document',
                        'Document Title', 
                        'Organization / Personnel', 
                        'Responsibility Text', 
                        'Other Organization(s) / Personnel Mentioned', 
                        'Documents Referenced']]
    
    final_df.to_csv(args.output_csv, index=False)
    # df.to_csv(args.output_csv, index=False)

    elapsed = time.time() - start

    logger.info("total time : {:}".format(cu.format_time(elapsed)))
