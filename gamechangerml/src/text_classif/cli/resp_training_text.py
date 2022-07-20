"""
usage: python table.py [-h] -i INPUT_DIR -a AGENCIES_FILE -o OUTPUT [-g GLOB]

Extracts responsibility statements from policy documents

optional arguments:
  -h, --help            show this help message and exit
  -i INPUT_DIR, --input-dir INPUT_DIR
                        corpus directory
  -a AGENCIES_FILE, --agencies-file AGENCIES_FILE
                        the magic agencies file
  -o OUTPUT, --output OUTPUT
                        name of the output file (.csv)
  -g GLOB, --glob GLOB  file glob to use in extracting from input_dir
"""
import logging
import re

import pandas as pd
from nltk.tokenize import sent_tokenize

import gamechangerml.src.utilities.spacy_model as spacy_m
from gamechangerml.src.featurization.table import Table

logger = logging.getLogger(__name__)


def wc(text):
    return text.count(" ") + 1


class ExtractRespText(Table):
    def __init__(self, input_dir, output, spacy_model, agency_file, glob):
        super(ExtractRespText, self).__init__(
            input_dir, output, spacy_model, agency_file, glob, True
        )
        logger.info("input dir : {}".format(input_dir))
        self.train_df = pd.DataFrame(columns=["source", "label", "text"])

        # matches 3.2.3., etc. at the start of the text
        self.dd_re = re.compile("(^\\d\\..*?\\d+\\. )")
        self.kw = "shall"
        self.resp = "RESPONSIBILITIES"

    def scrubber(self, txt):
        txt = re.sub("[\\n\\t\\r]+", " ", txt)
        txt = re.sub("\\s{2,}", " ", txt).strip()
        mobj = self.dd_re.search(txt)
        if mobj:
            txt = txt.replace(mobj.group(1), "")
        return txt.strip()

    def extract_positive(self):
        for tmp_df, fname in self.extract_section(self.input_dir):
            if 2 in tmp_df:
                tmp_df = tmp_df[2].drop_duplicates()
                pos_ex = [self.scrubber(txt) for txt in tmp_df.tolist()]
                pos_ex = [txt for txt in pos_ex if txt]
                yield pos_ex, fname, self.raw_text

    def extract_neg_in_doc(self, raw_text, min_len):
        neg_sentences = list()
        negs = 0
        if self.resp in raw_text:
            prev_text = raw_text.split(self.resp)[0]
            if prev_text is not None:
                sents = [
                    self.scrubber(sent)
                    for sent in sent_tokenize(prev_text)
                    if len(sent) > min_len
                ]
                negs += len(sents)
                neg_sentences.extend(sents)
        return neg_sentences

    def _append_df(self, source, label, texts):
        for txt in texts:
            if not txt:
                continue
            new_row = {
                "source": source,
                "label": label,
                "text": self.scrubber(txt),
            }
            self.train_df = self.train_df.append(new_row, ignore_index=True)

    def extract_pos_neg(self, min_len):
        total_pos = 0
        total_neg = 0
        for pos_ex, fname, raw_text in self.extract_positive():
            try:
                neg_ex = self.extract_neg_in_doc(raw_text, min_len=min_len)
                total_neg += len(neg_ex)
                self._append_df(fname, 0, neg_ex)
                logger.info(
                    "{:>35s} : {:3d} +, {:3d} -".format(
                        fname, len(pos_ex), len(neg_ex)
                    )
                )
            except ValueError as e:
                logger.exception("offending file name : {}".format(fname))
                logger.exception("{}: {}".format(type(e), str(e)))
                pass
        logger.info("positive samples : {:>6,d}".format(total_pos))
        logger.info("negative samples : {:>6,d}".format(total_neg))
        no_resp_docs = "\n".join(self.no_resp_docs)
        logger.info("no responsibilities : \n{}".format(no_resp_docs))


if __name__ == "__main__":
    from argparse import ArgumentParser

    log_fmt = (
        "[%(asctime)s %(levelname)-8s], [%(filename)s:%(lineno)s - "
        + "%(funcName)s()], %(message)s"
    )
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    desc = "Extracts responsibility statements from policy documents"
    parser = ArgumentParser(prog="python table.py", description=desc)

    parser.add_argument(
        "-i",
        "--input-dir",
        dest="input_dir",
        type=str,
        required=True,
        help="corpus directory",
    )
    parser.add_argument(
        "-a",
        "--agencies-file",
        dest="agencies_file",
        type=str,
        required=True,
        help="the magic agencies file",
    )
    parser.add_argument(
        "-o",
        "--output",
        dest="output",
        type=str,
        required=True,
        help="name of the output file (.csv)",
    )
    parser.add_argument(
        "-g",
        "--glob",
        dest="glob",
        type=str,
        default="DoDD*.json",
        help="file glob to use in extracting from input_dir",
    )

    args = parser.parse_args()

    logger.info("loading spaCy")
    spacy_model_ = spacy_m.get_lg_vectors()
    logger.info("spaCy loaded...")

    extract_obj = ExtractRespText(
        args.input_dir,
        args.output,
        spacy_model_,
        args.agencies_file,
        args.glob,
    )

    extract_obj.extract_pos_neg(min_len=1)
    logger.info(extract_obj.train_df.head())
    extract_obj.train_df.to_csv(
        args.output, index=False, header=False, doublequote=True
    )
