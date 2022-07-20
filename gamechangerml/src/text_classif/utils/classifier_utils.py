# The MIT License (MIT)
# Subject to the terms and conditions contained in LICENSE
import datetime
import fnmatch
import json
import logging
import os
import re

import numpy as np
import pandas as pd
from nltk.tokenize import sent_tokenize

logger = logging.getLogger(__name__)
here = os.path.dirname(os.path.realpath(__file__))

# sentence parsers have a hard time with abbreviations like U.S.C. and P.L.
# due to the multiple letter-period sequence, and so it breaks the line. This
# gets around the problem in `make_sentences()`.
USC_DOT = "U.S.C."
USC = "USC"
# P.L. is expressed both ways, so we go with "P. L.".
PL = "P.L."
PL_SPACE = "P. L."
EO = "E.O."
EO_SPACE = "E. O."
USC_RE = "\\b" + USC + "\\b"

dd_re = re.compile("(^\\d\\..*?\\d+\\. )")

# TODO consolidate these into something better


def next_pow_two(max_sent_tokens):
    """
    Next power of two for a given input, with a minimum of 16 and a
    maximum of 512

    Args:
        max_sent_tokens (int): the integer

    Returns:
        int: the appropriate power of two
    """
    pow_two = [16, 32, 64, 128, 256, 512]
    if max_sent_tokens <= pow_two[0]:
        return pow_two[0]
    if max_sent_tokens >= pow_two[-1]:
        return pow_two[-1]
    check = [max_sent_tokens > j for j in pow_two]
    idx = check.index(False)
    return pow_two[idx]


def flatten_labels(preds, labels):
    pred_flat = np.argmax(preds, axis=1).flatten()
    labels_flat = labels.flatten()
    return pred_flat, labels_flat


def format_time(elapsed):
    elapsed_rounded = int(round(elapsed))
    return str(datetime.timedelta(seconds=elapsed_rounded))


def cola_data(data_file):
    try:
        df = pd.read_csv(
            os.path.join(data_file),
            delimiter="\t",
            header=None,
            names=["src", "label", "l_notes", "sentence"],
        )
        df = df.sample(frac=1)
        sents = df.sentence.values
        labels = df.label.values
        return sents, labels
    except FileNotFoundError as e:
        logger.fatal("{} : {}".format(type(e), str(e)))
        logger.fatal("\n\n\tThat was a fatal error my friend")
        raise e


def _read_gc_df(data_file):
    df = pd.read_csv(
        data_file,
        delimiter=",",
        header=None,
        names=["src", "label", "sentence"],
    )
    return df


def gc_data(data_file, neg_data_file, shuffle=True, topn=0):
    try:
        df = _read_gc_df(data_file)
        pos_samples = np.sum(df.label.values)
        logger.info("positive samples : {:>5,d}".format(pos_samples))
        neg_samples = len(df.label.values) - pos_samples
        logger.info("negative samples : {:>5,d}".format(neg_samples))

        # balance positive / negative samples
        if neg_data_file is not None and pos_samples > neg_samples:
            df_neg = _read_gc_df(neg_data_file)
            df_neg = df_neg.sample(frac=1)
            logger.info("negative samples read : {:>5,d}".format(len(df_neg)))
            neg_to_get = pos_samples - neg_samples
            logger.info("adding negative samples : {:>5,d}".format(neg_to_get))
            neg_train_df = df_neg.head(neg_to_get)
            df = df.append(neg_train_df, ignore_index=True)

        if shuffle:
            df = df.sample(frac=1)
        if topn > 0:
            df = df.head(topn)
        sents = df.sentence.values
        labels = df.label.values
        src = df.src.values
        return sents, labels, src
    except FileNotFoundError as e:
        logger.fatal("\n{} : {}".format(type(e), str(e)))
        logger.fatal("\n\n\tThat was a fatal error my friend")
        raise e


def gen_gc_docs(doc_path, glob, key="raw_text"):
    file_list = [f for f in os.listdir(doc_path) if fnmatch.fnmatch(f, glob)]
    logger.debug("num files : {:>3,d}".format(len(file_list)))
    if len(file_list) == 0:
        logger.warning(
            "no files in '{}' matching the glob '{}'".format(doc_path, glob)
        )
    for input_file in sorted(file_list):
        with open(os.path.join(doc_path, input_file)) as fin:
            jdoc = json.load(fin)
            if key in jdoc:
                yield input_file, jdoc
            else:
                logger.warning("`{}` not found in {}".format(key, input_file))


def nfiles_in_glob(src_path, glob):
    return len([f for f in os.listdir(src_path) if fnmatch.fnmatch(f, glob)])


def load_data(data_file, n_samples, shuffle=False):
    """
    Loads the `data_file` (`.csv`) of sentence, labels and tacks on the
    source of the data. `n_samples` > 0 are returned as a list of
    dictionaries with keys 'src', 'label', 'sentence'.

    Args:
        data_file (str):
        n_samples (int):
        shuffle (bool):

    Returns:
        List[Dict]
    """
    df = pd.read_csv(data_file, columns=["src", "label", "sentence"])
    if "sentence" not in df.keys():
        raise AttributeError("no column labeled 'sentence' in data_file")
    if "label" not in df.keys():
        raise AttributeError("no column labeled 'label' in data_file")
    else:
        df["label"] = df["label"].astype(int)
    if shuffle:
        df = df.sample(frac=1)
    if n_samples > 0:
        df = df.head(n_samples)

    _, csv_name = os.path.split(data_file)

    examples = [
        {
            "src": row["src"],
            "label": row["label"],
            "sentence": row["sentence"],
        }
        for _, row in df.iterrows()
    ]
    return examples


def scrubber(txt, no_sec=False):
    txt = re.sub("[\\n\\t\\r]+", " ", txt)
    txt = re.sub("\\s{2,}", " ", txt).strip()
    if no_sec:
        mobj = dd_re.search(txt)
        if mobj:
            txt = txt.replace(mobj.group(1), "").strip()
    return txt


def _extract_batch_length(preds):
    """
    Extracts batch length of predictions.
    """
    batch_length = None
    for key, value in preds.items():
        batch_length = batch_length or value.shape[0]
        if value.shape[0] != batch_length:
            raise ValueError(
                "Batch length of predictions should be same. () has "
                "different batch length than others.".format(key)
            )
    return batch_length


def unbatch_preds(preds):
    """
    Unbatch predictions, as in estimator.predict().

    Args:
      preds: Dict[str, np.array], where all arrays have the same first
        dimension.

    Yields:
      sequence of Dict[str, np.array], with the same keys as preds.
    """
    if not isinstance(preds, dict):
        for pred in preds:
            yield pred
    else:
        for i in range(_extract_batch_length(preds)):
            yield {key: value[i] for key, value in preds.items()}


def new_df():
    return pd.DataFrame(columns=["src", "label", "sentence"])


def make_sentences(text, src):
    """
    Builds a list of dictionaries, one for each sentence resulting from
    the sentence parser. The dictionary schema is

        {"src": src, "label": 0, "sentence": sent}

    Substitutions are made for the identified tokens.

    Args:
        text (str): text to process
        src (str): identifier (file name) to include in the output

    Returns:
        List[Dict]
    """
    no_sec = True
    text = text.replace(USC_DOT, USC)
    text = text.replace(PL, PL_SPACE)
    text = text.replace(EO, EO_SPACE)
    sents = [scrubber(sent, no_sec=no_sec) for sent in sent_tokenize(text)]
    sent_list = list()
    for sent in sents:
        if not sent:
            continue
        sent_list.append({"src": src, "label": 0, "sentence": sent})
    return sent_list


def raw2dict(src_path, glob, key="raw_text"):
    """
    Generator to step through `glob` and extract each file's sentences;
    Wrapper for `make_sentence()`.

    Args:
        src_path (str): location of the .json documents

        glob (str): file pattern to match

        key (str): text key in the .json

    Yields:
        List[Dict]: per the schema in `make_sentences()`
        str: name of the file
    """
    for fname, doc in gen_gc_docs(src_path, glob, key=key):
        title = doc["title"]
        source = doc["filename"]
        raw_text = doc["raw_text"]
        sent_list = make_sentences(raw_text, fname)
        for sent in sent_list:
            sent.update({"title": title, "source": source})
        logger.debug(
            "{:>40s} : {:>5,d} sentences".format(fname, len(sent_list))
        )
        yield sent_list, fname
