import logging
import os
import time

from tqdm import tqdm

import gamechangerml.src.text_classif.utils.classifier_utils as cu
from gamechangerml.src.text_classif.predictor import Predictor

logger = logging.getLogger(__name__)


def _predict_docs(input_dicts, predictor, max_seq_len, batch_size):
    adder = 0
    if len(input_dicts) % batch_size != 0:
        adder = 1
    batches = len(input_dicts) // batch_size + adder
    out_list = list()
    start = time.time()
    for output in tqdm(
        predictor.predict(
            input_dicts,
            batch_size=int(batch_size),
            max_seq_len=int(max_seq_len),
        ),
        desc="predict",
        total=batches,
    ):
        out_list.extend(output)

    elapsed = time.time() - start
    if len(out_list) > 0:
        rate = elapsed / len(out_list)
    else:
        rate = 0.0
    logger.info("       time : {:}".format(cu.format_time(elapsed)))
    logger.info("time / text :{:>6.3f} secs".format(rate))
    return out_list


def predict_glob(
    model_path_name, data_path, glob, max_seq_len=128, batch_size=8
):
    """
    This generator performs classification on `.json` corpus docs using
    the `raw_text` key in a `.json` document.

    The text is passed through the spaCy "sentencizer" to create a list of
    dictionaries, one for each extracted sentence.

    Batches(`batch_size`) of these dictionaries are sent forward through the
    model(`model_name_path`) with the predicted class and p(class) assembled
    in a dictionary and returned on iteration.

    This assumes the model directory is laid out per Hugging Face, i.e.,
        - `config.json`
        - `pytorch_model.bin`
        - etc.

    Args:
        model_path_name (str): path of the checkpointed model

        data_path (str): path containing the .json corpus files

        glob (str): file pattern to match, e.g., DoDD*.json

        max_seq_len (int): max number of tokens after encoding; default=128

        batch_size (int): batch size

    Yields:
        List[Dict]

    Raises:
        ValueError if the arguments are incorrect
        FileNotFoundError if the checkpoint model path is incorrect

    """
    if not os.path.isdir(data_path):
        raise ValueError("no directory named '{}'".format(data_path))
    if not 128 <= max_seq_len <= 512:
        raise ValueError("invalid max_seq_len; got {}".format(max_seq_len))
    if batch_size < 8:
        raise ValueError("invalid batch_size; got {}".format(batch_size))
    if not glob.strip():
        raise ValueError("invalid file glob; got '{}'".format(glob))
    if not os.path.isfile(os.path.join(model_path_name, "config.json")):
        raise FileNotFoundError("model_path_name has no 'config.json'")

    predictor = Predictor(model_path_name, num_labels=2)

    for input_dicts, fname in cu.raw2dict(data_path, glob, key="raw_text"):
        out_list = _predict_docs(
            input_dicts, predictor, max_seq_len, batch_size
        )
        yield out_list, fname
