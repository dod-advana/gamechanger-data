"""
usage: python predict_glob.py [-h] -m MODEL_PATH -d DATA_PATH [-b BATCH_SIZE]
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
import re

from tqdm import tqdm

import dataScience.src.utilities.spacy_model as spacy_m
from dataScience.src.text_classif.utils.log_init import initialize_logger
from dataScience.src.text_classif.utils.predict_glob import predict_glob

logger = logging.getLogger(__name__)

RESP = "RESPONSIBILITIES"
SENTENCE = "sentence"
KW = "shall"
KW_RE = "\\b" + KW + ":?\\b"
NA = "NA"
TC = "top_class"
ENT = "entity"
new_edict = {ENT: NA}


def contains_entity(text, nlp):
    entities = [
        ent.text for ent in nlp(text).ents if ent.label_ in ["PERSON", "ORG"]
    ]
    if entities:
        logger.debug("\ttext : {}".format(text))
        logger.debug("\textracted entity : {}".format(list(set(entities))))
        return list(set(entities))
    else:
        return False


def _attach_entity(output_list, entity_list, nlp):
    curr_entity = NA
    for entry in tqdm(output_list, desc="entity"):
        logger.debug(entry)
        sentence = entry[SENTENCE]
        new_entry = new_edict
        new_entry.update(entry)
        if KW in sentence:
            curr_entity = re.split(KW_RE, sentence)[0].strip()
            entities = contains_entity(curr_entity, nlp)
            if not entities:
                curr_entity = NA
            logger.debug("current entity : {}".format(curr_entity))

        if entry[TC] == 1:
            new_entry[ENT] = curr_entity
        entity_list.append(new_entry)


def _populate_entity(output_list, nlp):
    entity_list = list()
    for idx, entry in enumerate(output_list):
        e_dict = new_edict
        e_dict.update(entry)
        if e_dict[TC] == 0 and RESP in entry[SENTENCE]:
            entity_list.append(e_dict)
            _attach_entity(output_list[idx + 1 :], entity_list, nlp)
            return entity_list
        else:
            entity_list.append(e_dict)
    return entity_list


def make_table(
    model_path,
    data_path,
    glob,
    max_seq_len,
    batch_size,
    nlp,
):
    # a list entry looks like:
    # {'top_class': 0, 'prob': 0.997, 'src': 'DoDD 5105.21.json', 'label': 0,
    #  'sentence': 'Department of...'}
    # --> `top_class` is the predicted label
    pop_ent = list()
    for output_list, file_name in predict_glob(
        model_path, data_path, glob, max_seq_len, batch_size
    ):
        logger.info("num input : {:,}".format(len(output_list)))
        pop_ent = _populate_entity(output_list, nlp)
        logger.info("processed : {:,}  {}".format(len(pop_ent), file_name))
    return pop_ent


# CLI example
if __name__ == "__main__":
    import logging
    import time
    from argparse import ArgumentParser
    import pandas as pd

    import dataScience.src.text_classif.utils.classifier_utils as cu

    desc = "Binary classification of each sentence in the files "
    desc += "matching the 'glob' in data_path"
    parser = ArgumentParser(prog="python predict_glob.py", description=desc)
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
        default="sample_entity.csv",
        help="the .csv for output",
    )

    initialize_logger(to_file=False, log_name="none")

    args = parser.parse_args()

    logger.info("loading spaCy")
    nlp_ = spacy_m.get_lg_nlp()

    start = time.time()
    out_list = make_table(
        args.model_path,
        args.data_path,
        args.glob,
        args.max_seq_len,
        args.batch_size,
        nlp=nlp_,
    )
    elapsed = time.time() - start
    logger.info(" total time : {:}".format(cu.format_time(elapsed)))

    df = pd.DataFrame(out_list)
    df.to_csv(args.output_csv, index=False)
