# The MIT License (MIT)
# Subject to the terms and conditions contained in LICENSE
import datetime
import fnmatch
import logging
import json
import os
import re

import numpy as np
import pandas as pd
from tqdm import tqdm

logger = logging.getLogger(__name__)
here = os.path.dirname(os.path.realpath(__file__))
nlp_ = None


def next_pow_two(max_sent_tokens):
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


def gc_data_item_labels(data_file, cp=0.50, cm=0.50, shuffle=True, topn=0):
    out_df = pd.DataFrame(columns=["src", "label", "sentence"])
    alpha = list("abcdefghijklmnopqrstuvwxyz0123456789")
    try:
        df = _read_gc_df(data_file)
        if shuffle:
            df = df.sample(frac=1)
        if topn > 0:
            df = df.head(topn)

        pos_samples = np.sum(df.label.values)
        logger.info("positive samples : {:>5,d}".format(pos_samples))
        neg_samples = len(df.label.values) - pos_samples
        logger.info("negative samples : {:>5,d}".format(neg_samples))

        # for positive samples that satisfy r'(^\w\. )', remove the item label
        for _, row in tqdm(df.iterrows()):
            src = row.src
            label = row.label
            sent = row.sentence
            if row.label == 1:
                mobj = re.search(r"(^\w\. |\(?\d+\) )", sent)
                if np.random.uniform() > 1.0 - cp:
                    if mobj is not None:
                        sent = re.sub(re.escape(mobj.group(1)), "", sent)
            else:  # randomly add an item label
                mobj = re.search(r"(^\w\. )", sent)
                if np.random.uniform() > 1.0 - cm:
                    if mobj is None:
                        idx = np.random.randint(0, len(alpha))
                        sent = alpha[idx] + ". " + sent

            out_df = out_df.append(
                {"src": src, "label": label, "sentence": sent},
                ignore_index=True,
            )
        logger.info("writing file...")
        out_df.to_csv(
            "dodi_dodd_train_lbl_flipped.csv", index=False, header=False
        )

        sents = out_df.sentence.values
        labels = out_df.label.values
        src = out_df.src.values
        return sents, labels, src
    except FileNotFoundError as e:
        logger.fatal("{} : {}".format(type(e), str(e)))
        logger.fatal("\n\n\tThat was a fatal error my friend")
        raise e


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


def gc_data_tvt(data_file, topn=0, ident="", split=0.90):
    try:
        df = _read_gc_df(data_file)
        if topn > 0:
            df = df.head(topn)
        pos_lbl = 0
        pos = 0
        for _, row in df.iterrows():
            if row.label == 1:
                pos += 1
                if re.search(r"^\w\. ", row.sentence) is not None:
                    pos_lbl += 1
        logger.info("item label positives {:,} / {:,}".format(pos_lbl, pos))
        # 80, 10, 10 split
        train, validate, test = np.split(
            df.sample(frac=1), [int(0.8 * len(df)), int(0.9 * len(df))]
        )
        logger.info("train : {:>5,d}".format(len(train)))
        logger.info("  val : {:>5,d}".format(len(validate)))
        logger.info(" test : {:>5,d}".format(len(test)))
        train.to_csv(
            os.path.join(here, "train_" + ident + ".csv"),
            sep=",",
            index=False,
            header=False,
        )
        validate.to_csv(
            os.path.join(here, "validate_" + ident + ".csv"),
            sep=",",
            index=False,
            header=False,
        )
        test.to_csv(
            os.path.join(here, "test_" + ident + ".csv"),
            sep=",",
            index=False,
            header=False,
        )
        return train, validate, test
    except FileNotFoundError as e:
        logger.fatal("\n{} : {}".format(type(e), str(e)))
        logger.fatal("\n\n\tThat was a fatal error my friend")
        raise e


def gen_gc_docs(doc_path_, glob, key="raw_text"):
    file_list = [f for f in os.listdir(doc_path_) if fnmatch.fnmatch(f, glob)]
    logger.info("num files : {:>3,d}".format(len(file_list)))
    for input_f in sorted(file_list):
        with open(os.path.join(doc_path_, input_f)) as fin:
            jdoc = json.load(fin)
            if key in jdoc:
                yield jdoc[key], input_f
            else:
                logger.warning("`{}` not found in {}".format(key, input_f))


def load_data(data_file, n_samples, shuffle=False):
    df = pd.read_csv(data_file)
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


def scrubber(txt):
    txt = re.sub("[\\n\\t\\r]+", " ", txt)
    txt = re.sub("\\s{2,}", " ", txt)
    return txt.strip()


def _extract_batch_length(preds):
    """
    Extracts batch length of predictions.
    """
    batch_length = None
    for key, value in preds.items():
        batch_length = batch_length or value.shape[0]
        if value.shape[0] != batch_length:
            raise ValueError(
                "Batch length of predictions should be same. %s has "
                "different batch length than others." % key
            )
    return batch_length


def unbatch_preds(preds):
    """
    Unbatch predictions, as in estimator.predict().

    Args:
      preds: Dict[str, np.ndarray], where all arrays have the same first
        dimension.
    Yields:
      sequence of Dict[str, np.ndarray], with the same keys as preds.
    """
    if not isinstance(preds, dict):
        for pred in preds:
            yield pred
    else:
        for i in range(_extract_batch_length(preds)):
            yield {key: value[i] for key, value in preds.items()}
