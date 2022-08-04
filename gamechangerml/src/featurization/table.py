import json
import fnmatch
import logging
import os
import re

import numpy as np
import pandas as pd

import gamechangerml.src.utilities.spacy_model as spacy_
from gamechangerml.src.featurization.ref_list import collect_ref_list
from gamechangerml.src.featurization.abbreviations_utils import (
    get_agencies_dict,
    check_duplicates,
    get_agencies,
)
from gamechangerml.src.featurization.extract_improvement.extract_utils import (
    extract_entities,
    create_list_from_dict,
    remove_articles,
    match_parenthesis,
)

logger = logging.getLogger(__name__)


class Table:
    def __init__(
        self, input_dir, output, spacy_model, agency_file, glob, indicators
    ):
        self.input_dir = input_dir
        self.output = output
        self.spacy_model = spacy_model

        self.duplicates, self.aliases = get_agencies_dict(agency_file)
        self.df = pd.DataFrame(columns=["doc", "entity", 1, 2, 3])
        self.resp = "RESPONSIBILITIES"
        self.decimal_digits = r"(\d+)(?!.*\d)"
        self.glob = glob
        self.indicators = indicators

        # finds number decimal, number in parenthesis, letter decimal, and
        # letter in parenthesis at start of row
        self.find = (
            r"(^|\n)(\d+\.\d+\.|\d+\.|\(\s*\d+\s*\)|[a-z]\.|\(\s*[a-z]+\s*\))"
        )
        self.doc_dict = None
        self.raw_text = None
        self.no_resp_docs = list()

    def extract_all(self):
        for tmp_df, fname in self.extract_section(self.input_dir):
            self.df = self.df.append(tmp_df, ignore_index=True)
        self.df.to_csv(self.output)

    def extract_section(self, input_dir):
        count = 0
        for file in sorted(os.listdir(input_dir)):
            if not fnmatch.fnmatch(file, self.glob):
                continue
            with open(os.path.join(input_dir, file)) as f_in:
                try:
                    self.doc_dict = json.load(f_in)
                except json.JSONDecodeError:
                    logger.warning("could not decode `{}`".format(file))
                    continue
            file = self.doc_dict["filename"]
            text = self.doc_dict["raw_text"]
            self.raw_text = text
            count += 1
            if self.resp in text:
                resp_text, entity = self.get_section(text, file)
            else:
                continue
            self.it = re.sub(
                self.decimal_digits,
                lambda x: str(int(x.group(1)) - 1),
                self.next_it,
            )
            self.num = re.search(self.decimal_digits, self.it)
            if self.num:
                self.num = self.num[1]
            else:
                self.num = ""
            if "." in self.it and self.it + "1." in resp_text:
                temp_df, doc_dups = self.decimal_parse(resp_text, file, entity)
            else:
                temp_df, doc_dups = self.num_let_parse(resp_text, file, entity)
            temp_df["agencies"] = get_agencies(
                temp_df, doc_dups, self.duplicates, self.aliases
            )
            temp_df = self.get_entity_refs(temp_df)
            temp_df = self.get_agency(temp_df)
            # logger.info(
            #     "{:>25s} : {:>3,d}".format(
            #         self.doc_dict["filename"], len(temp_df)
            #     )
            # )
            if len(temp_df) == 0:
                self.no_resp_docs.append(self.doc_dict["filename"])
            yield temp_df, self.doc_dict["filename"]

    def get_section(self, text, file):
        new = text.rsplit("RESPONSIBILITIES", 1)[1].lstrip()
        prev = (
            text.rsplit("RESPONSIBILITIES", 1)[0]
            .strip()
            .split("\n")[-1]
            .strip()
        )
        self.next_it = re.sub(
            self.decimal_digits, lambda x: str(int(x.group(1)) + 1), prev
        )
        new = new.split("\n" + self.next_it + " ", 1)[0]
        new = new.split("GLOSSARY", 1)[0]
        entity = new.split(":", 1)[0]
        entity = entity.split("shall", 1)[0]
        entity = entity.split(".")[-1].strip()

        # get rid of headers
        header = r"\d*\s*" + file[:12] + "(.*)\n"

        new = re.sub(header, " ", new)
        return new, entity

    # check for list nested by additional decimals
    def decimal_parse(self, text, file, entity):
        temp_df = pd.DataFrame(columns=["doc", "entity", 1])
        splitted = re.split(r"\n\d+.", text)[1:]
        num = "0."
        level = 1
        cols = [file, entity, ""]
        doc_dups = []

        for i in splitted:
            if len(i.split()) > 1:
                this = i.split()[0]
            else:
                continue
            if this == re.sub(
                self.decimal_digits, lambda x: str(int(x.group(1)) + 1), num
            ):
                num = this
                if self.indicators:
                    text = self.it + i
                else:
                    text = i[i.index(" ") + 1 :]
                text = re.sub("\n", "", text)
                text = text.replace(entity, "", 1)

                cols.pop()
                temp_df = self.add_row(text, cols, temp_df)
            elif this == num + "1.":
                level += 1
                if level not in temp_df.columns:
                    temp_df[level] = ""
                num = this
                if self.indicators:
                    text = self.it + i
                else:
                    text = i[i.index(" ") + 1 :]
                text = re.sub("\n", "", text)
                text = text.replace(entity, "", 1)
                temp_df = self.add_row(text, cols, temp_df)
            else:
                if (".") not in this:
                    continue
                if level != 1:
                    for a in range(num.count(".") - this.count(".")):
                        level -= 1
                        cols.pop()
                num = this
                if self.indicators:
                    text = self.it + i
                else:
                    text = i[i.index(" ") + 1 :]
                text = re.sub("\n", "", text)
                text = text.replace(entity, "", 1)
                cols.pop()
                temp_df = self.add_row(text, cols, temp_df)
            doc_dups.append(
                check_duplicates(self.raw_text, self.duplicates, self.aliases)
            )
        return (temp_df, doc_dups)

    def add_row(self, text, cols, temp_df):
        cols.append(text)
        add = [""] * (len(temp_df.columns) - len(cols))
        temp_df.loc[len(temp_df)] = cols + add
        return temp_df

    # parse documents with nested different letter/number lists
    def num_let_parse(self, text, file, entity):
        vals = ["1", "a", "1", "a"]
        levels = [0, 0, 0, 0]
        level = 0
        cols = [file, entity]
        doc_dups = []
        temp_df = pd.DataFrame(columns=["doc", "entity"])
        found = re.split(self.find, text, 1)
        past = None
        prev = 0
        while len(found) > 1:
            it = found[2]
            if (
                vals[0] + "." == found[2]
                or self.num + "." + vals[0] + "." == found[2]
            ):
                if levels[0] == 0:
                    level += 1
                    levels[0] = level
                    if level < 4:
                        temp_df[level] = ""
                vals[0] = str(int(vals[0]) + 1)
                found = re.split(self.find, found[3], 1)
                for i in range(prev - levels[0]):
                    if levels[1] > levels[0]:
                        vals[1] = "a"
                    if levels[2] > levels[0]:
                        vals[2] = "1"
                    if levels[3] > levels[0]:
                        vals[3] = "a"
                    cols.pop()
                if prev >= levels[0]:
                    cols.pop()
                if self.indicators:
                    cols.append(it + found[0])
                else:
                    cols.append(found[0])
                prev = levels[0]
                temp_df = self.add_row2(temp_df, cols, levels[0])

            elif (
                vals[1] + "." in found[2]
                or chr(ord(vals[1]) + 1) + "." in found[2]
            ):
                if levels[1] == 0:
                    level += 1
                    if level < 4:
                        temp_df[level] = ""
                    levels[1] = level
                vals[1] = chr(ord(vals[1]) + 1)
                found = re.split(self.find, found[3], 1)
                for i in range(prev - levels[1]):
                    if levels[0] > levels[1]:
                        vals[0] = "1"
                    if levels[2] > levels[1]:
                        vals[2] = "1"
                    if levels[3] > levels[1]:
                        vals[3] = "a"
                    cols.pop()
                if prev >= levels[1]:
                    cols.pop()
                if self.indicators:
                    cols.append(it + found[0])
                else:
                    cols.append(found[0])
                prev = levels[1]
                temp_df = self.add_row2(temp_df, cols, levels[1])
            elif re.compile("\(\s*" + vals[2] + "\s*\)").search(found[2]):
                if levels[2] == 0:
                    level += 1
                    if level < 4:
                        temp_df[level] = ""
                    levels[2] = level
                vals[2] = str(int(vals[2]) + 1)
                found = re.split(self.find, found[3], 1)
                for i in range(prev - levels[2]):
                    if levels[1] > levels[2]:
                        vals[1] = "a"
                    if levels[3] > levels[2]:
                        vals[3] = "a"
                    if levels[0] > levels[2]:
                        vals[0] = "1"
                    cols.pop()
                if prev >= levels[2]:
                    cols.pop()
                if self.indicators:
                    cols.append(it + found[0])
                else:
                    cols.append(found[0])
                prev = levels[2]
                temp_df = self.add_row2(temp_df, cols, levels[2])
            elif re.compile("\(\s*" + vals[3] + "\s*\)").search(found[2]):
                if levels[3] == 0:
                    level += 1
                    if level < 4:
                        temp_df[level] = ""
                    levels[3] = level
                vals[3] = chr(ord(vals[3]) + 1)
                found = re.split(self.find, found[3], 1)
                for i in range(prev - levels[3]):
                    if levels[1] > levels[3]:
                        vals[1] = "a"
                    if levels[0] > levels[3]:
                        vals[0] = "1"
                    if levels[2] > levels[3]:
                        vals[3] = "1"
                    cols.pop()
                if prev >= levels[3]:
                    cols.pop()
                if self.indicators:
                    cols.append(it + found[0])
                else:
                    cols.append(found[0])
                prev = levels[3]
                temp_df = self.add_row2(temp_df, cols, levels[3])
            else:
                found = re.split(self.find, found[3], 1)
                if len(temp_df) > 0:
                    pop = cols.pop()
                    cols.append(pop + it + found[0])
                    add = [""] * (len(temp_df.columns) - len(cols))
                    if len(cols) > 5:
                        newcols = cols[0:2] + cols[-3:]
                        temp_df.iloc[-1] = newcols
                    else:
                        temp_df.iloc[-1] = cols + add

            doc_dups.append(
                check_duplicates(self.raw_text, self.duplicates, self.aliases)
            )
        return temp_df, doc_dups

    def add_row2(self, temp_df, cols, lev):
        add = [""] * (len(temp_df.columns) - len(cols))
        if lev > 3:
            newcols = cols[0:2] + cols[-3:]
            temp_df.loc[len(temp_df)] = newcols
        else:
            temp_df.loc[len(temp_df)] = cols + add
        return temp_df

    def get_entity_refs(self, df):
        # add agencies and references and update entities
        # df["agencies"] = ""
        combined_cols = pd.DataFrame(
            df[df.columns[2:5]].apply(
                lambda x: ",".join(x.dropna().astype(str)), axis=1
            ),
            columns=["text"],
        )
        df["ref"] = ""
        for i, row in combined_cols.iterrows():

            if isinstance(row["text"], str):
                first = row["text"].split(".", 1)[0]
                if sum(1 for c in first if c.isupper()) > sum(
                    1 for a in first if a.islower()
                ):
                    df.at[i, "entity"] = first
                elif ":" in row["text"]:
                    if "shall" in row["text"].split(":", 1)[0]:
                        if (
                            row["text"]
                            .split("shall")[0]
                            .strip()
                            .split(" ")[-1]
                            == "and"
                        ):
                            continue
                        entity = row["text"].split(":", 1)[0]
                        entity = entity.split("shall", 1)[0]
                        entity = entity.split(".")[-1].strip()
                        df.at[i, "entity"] = entity

            refs = []

            if type(row["text"]) == str:
                refs.append(list(collect_ref_list(row["text"]).keys()))
            flat_r = [item for sublist in refs for item in sublist]
            flat_r = "|".join(list(set(flat_r)))
            df.at[i, "ref"] = flat_r
        return df

    def get_agency(self, df):
        df["agencies"].replace(np.nan, "", regex=True, inplace=True)
        combined_cols = pd.DataFrame(
            df[df.columns[1:]].apply(
                lambda x: ",".join(x.dropna().astype(str)), axis=1
            ),
            columns=["text"],
        )
        combined_cols_list = combined_cols["text"].tolist()
        all_docs = []

        for i in range(len(combined_cols_list)):
            sentence = combined_cols_list[i]
            entities = extract_entities(sentence, self.spacy_model)

            prev_agencies = [x.strip() for x in df["agencies"][i].split(",")]
            prev_agencies = [i for i in prev_agencies if i]

            flat_entities = create_list_from_dict(entities)
            for j in prev_agencies:
                flat_entities.append(j)

            flat_entities = remove_articles(flat_entities)
            flat_entities = match_parenthesis(flat_entities)
            flat_entities = "|".join(i for i in set(flat_entities))
            all_docs.append(flat_entities)

        df["agencies"] = all_docs
        return df


if __name__ == "__main__":
    from argparse import ArgumentParser

    log_fmt = (
        "[%(asctime)s %(levelname)-8s], [%(filename)s:%(lineno)s - "
        + "%(funcName)s()], %(message)s"
    )
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    logger.info("loading spaCy")
    spacy_model_ = spacy_.get_lg_nlp()
    logger.info("spaCy loaded...")

    desc = "Extracts responsibility statements from policy documents"
    parser = ArgumentParser(usage="python table.py", description=desc)

    parser.add_argument(
        "-i", "--input-dir", dest="input_dir", type=str, required=True
    )
    parser.add_argument(
        "-a", "--agencies-file", dest="agencies_file", type=str, required=True
    )
    parser.add_argument(
        "-o", "--output", dest="output", type=str, required=True
    )
    parser.add_argument(
        "-g", "--glob", dest="glob", type=str, default="DoD*.json"
    )
    parser.add_argument(
        "-n", "--indicators", dest="indicator", action="store_true"
    )
    parser.set_defaults(indicator=False)

    args = parser.parse_args()

    table_obj = Table(
        args.input_dir,
        args.output,
        spacy_model_,
        args.agencies_file,
        args.glob,
        args.indicator,
    )

    table_obj.extract_all()
