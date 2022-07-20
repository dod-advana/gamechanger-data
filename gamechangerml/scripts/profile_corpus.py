import json
import argparse
import os
from os import listdir
from os.path import isfile, join
import time
from datetime import datetime
import pandas as pd
import numpy as np
import functools
from gensim.parsing.preprocessing import STOPWORDS
from gensim.utils import simple_preprocess
from transformers import BertTokenizer
#from gamechangerml.src.text_handling.process import preprocess, bert_tokenizer
from gamechangerml import REPO_PATH

columns = [
    "filename",  # filename
    "doc_type",  # doc type
    "char_len",  # doc character length
    "num_par",  # number of paragraphs
    "doc_token_gensim",  # number of tokens (using Gensim tokenizer)
    "doc_token_bert",  # number of tokens (using Bert tokenizer)
    "par_token_gensim",  # number of Gensim tokens per paragraph
    "par_token_bert",  # number of Bert tokens per paragraph
    "par_char_len",  # paragraph character length
]

column_names = ",".join(columns)

## copied from gamechangerml.src.text_handling.process
class bert_tokenizer(object):
    def __init__(self,
                 vocab_file):
        
        self.vocab_file = vocab_file
        self.tokenizer = BertTokenizer(vocab_file = self.vocab_file, do_lower_case = True)

    def tokenize(self, text):
        tokens = self.tokenizer.tokenize(text)

        return tokens, len(tokens)

## copied from gamechangerml.src.text_handling.process
def preprocess(
    text,
    min_len=2,
    phrase_detector=None,
    remove_stopwords=False,
    additional_stopwords=None,
):
    """
        preprocess - standard text processing (possibly break out more if complex preprocessing needed
        Args:
            text (str)
            min_len (int): optional Minimum length of token (inclusive). Shorter tokens are discarded.
            remove_stopwords (bool)
            additional_stopwords (list of strings)
        Returns:
            tokens (list of strings)
    """
    tokens = simple_preprocess(text, min_len=min_len, max_len=20)

    if phrase_detector != None:
        tokens = phrase_detector.apply(tokens)

    if remove_stopwords:
        if additional_stopwords != None:
            stopwords_list = STOPWORDS.union(set(additional_stopwords))
        else:
            stopwords_list = STOPWORDS
        tokens = [word for word in tokens if word not in stopwords_list]

    return tokens

def name_outputs(corpus_files):

    today = datetime.today().strftime("%Y-%m-%d")
    name = "./corpus_stats_" + today + "_" + str(len(corpus_files))

    return name + ".csv", name + ".txt"


def open_file(filename, path):
    with open(join(path, filename)) as f:
        return json.load(f)


def get_doc_stats(file):

    doc = open_file(file, corpus_dir)
    text = doc["text"]

    p_gensim_tokens = []
    p_bert_tokens = []
    p_char = []

    for i in range(len(doc["paragraphs"])):
        p = doc["paragraphs"][i]["par_raw_text_t"]
        p_char.append(str(len(p)))
        p_gensim_tokens.append(str(len(preprocess(p))))
        p_bert_tokens.append(str(bert_token.tokenize(p)[1]))

    p_gensim_tokens = "; ".join(p_gensim_tokens)
    p_bert_tokens = "; ".join(p_bert_tokens)
    p_char = "; ".join(p_char)

    doc_stats = [
        file,  # filename
        doc["doc_type"],  # doc type
        len(doc["text"]),  # length of text in char
        len(doc["paragraphs"]),  # number of paragraphs
        len(preprocess(text)),  # length gensim tokenized
        bert_token.tokenize(text)[1],  # length bert tokenized
        p_gensim_tokens,  # list of gensim tokenized paragraph lengths
        p_bert_tokens,  # list of bert tokenized paragraph lengths
        p_char,  # list of paragraph lengths (characters)
    ]

    doc_stats = [str(i) for i in doc_stats]

    return "\n" + ",".join(doc_stats)


def get_paragraph_stats(df):

    gensim_pars = []
    for x in df["par_token_gensim"]:
        if type(x) == str:
            x = x.lstrip("[").strip("]").split(";")
            x = [int(i.strip().lstrip()) for i in x]
        gensim_pars.extend(x)

    gensim_pars.sort()

    bert_pars = []
    for x in df["par_token_bert"]:
        if type(x) == str:
            x = x.lstrip("[").strip("]").split(";")
            x = [int(i.strip().lstrip()) for i in x]
        bert_pars.extend(x)

    bert_pars.sort()

    return gensim_pars, bert_pars


def get_vocab(df):

    fulltext = ""
    vocab_dict = {}
    srcs = list(df["source"].unique())
    for i in srcs:

        sub = df[df["source"] == i]
        subtext = ""
        for j in sub["filename"]:

            text = open_file(j, corpus_dir)["text"]

            subtext += " " + text
            fulltext += " " + text

        sub_tokens = len(set(preprocess(subtext)))

        vocab_dict[i] = sub_tokens

    full_tokens = len(set(preprocess(fulltext)))
    full_tokens_stop = len(set(preprocess(fulltext, remove_stopwords=True)))

    return vocab_dict, full_tokens, full_tokens_stop


def get_agg_df(df, vocab_dict):

    agg_dfs = [
        df.groupby("source")
        .agg({"doc_type": "count"})
        .reset_index()[["source", "doc_type"]],
        df.groupby("source").count().reset_index()[["source", "filename"]],
        df.groupby("source")
        .agg({"doc_token_gensim": "sum"})
        .reset_index()[["source", "doc_token_gensim"]],
        df.groupby("source")
        .agg({"doc_token_gensim": "mean"})
        .reset_index()[["source", "doc_token_gensim"]],
        df.groupby("source")
        .agg({"doc_token_gensim": "median"})
        .reset_index()[["source", "doc_token_gensim"]],
        df.groupby("source")
        .agg({"doc_token_bert": "median"})
        .reset_index()[["source", "doc_token_bert"]],
        df.groupby("source")
        .agg({"doc_token_gensim": "std"})
        .reset_index()[["source", "doc_token_gensim"]],
        df.groupby("source")
        .agg({"num_par": "sum"})
        .reset_index()[["source", "num_par"]],
        df.groupby("source")
        .agg({"num_par": "mean"})
        .reset_index()[["source", "num_par"]],
        df.groupby("source")
        .agg({"num_par": "median"})
        .reset_index()[["source", "num_par"]],
        df.groupby("source")
        .agg({"num_par": "std"})
        .reset_index()[["source", "num_par"]],
    ]

    agg = functools.reduce(
        lambda left, right: pd.merge(left, right, on="source", how="outer"), agg_dfs
    )

    agg.columns = [
        "source",
        "doc_type",
        "number_docs",
        "total_tokens",
        "mean_tokens",
        "median_tokens_gensim",
        "median_tokens_bert",
        "std_tokens",
        "total_paragraphs",
        "mean_paragraphs",
        "median_paragraphs",
        "std_paragraphs",
    ]

    agg["unique_vocab"] = agg["source"].map(vocab_dict)

    agg = agg.sort_values(by="number_docs", ascending=False)

    return agg


def join_df(corpus_profile: pd.DataFrame, sources: pd.DataFrame) -> pd.DataFrame:

    df = corpus_profile.merge(sources, on="doc_type", how="inner")
    df["group"].fillna("Misc.", inplace=True)

    return df


def format_counts(sub, sources):

    count = sub.groupby("doc_type").count().reset_index()
    count = count[["doc_type", "filename"]]
    count = count.merge(sources, on="doc_type")
    count.sort_values(by="filename", ascending=False, inplace=True)
    count.rename(
        columns={"doc_type": "Doc Type", "filename": "# Documents", "source": "Source"},
        inplace=True,
    )

    return count[["Doc Type", "Source", "# Documents", "Description"]]

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Profile Corpus")

    parser.add_argument("--corpus", "-c", dest="corpus", help="local corpus dir")
    parser.add_argument("--save_dir", "-d", dest="save_dir", help="directory to save outputs")

    args = parser.parse_args()

    corpus_dir = args.corpus
    save_dir = args.save_dir
    bert_vocab = os.path.join(REPO_PATH, "gamechangerml/src/text_handling/assets/bert_vocab.txt")
    sources_path = os.path.join(REPO_PATH, "gamechangerml/scripts/corpus_doctypes.csv")
    #save_dir = os.path.join(REPO_PATH, "gamechangerml/scripts/stats_output/")

    if not os.path.exists(save_dir):  # make dir to save files
        os.makedirs(save_dir)

    bert_token = bert_tokenizer(bert_vocab)
    corpus_files = [f for f in listdir(corpus_dir) if isfile(join(corpus_dir, f))]

    print("\n|--------------Generating stats csv---------------|\n")

    start = time.time()
    doc_count = 0
    csv_path, txt_path = name_outputs(corpus_files)
    stats_csv = open(join(save_dir, csv_path), "w")
    stats_csv.write(column_names)

    for i in corpus_files:

        doc_count += 1
        print(doc_count, i)
        row = get_doc_stats(i)
        stats_csv.write(row)

    stats_csv.close()

    end = time.time()
    print("Time to process csv: ", (end - start) / 60, " minutes")

    print("\n|--------------Getting vocabularies---------------|\n")

    start = time.time()

    dtypes = pd.read_csv(sources_path)
    profile = pd.read_csv(join(save_dir, csv_path))
    profile = join_df(profile, dtypes)

    groups = list(profile["group"].unique())
    sources = list(profile["source"].unique())

    vocab_dict, full_tokens, full_tokens_stop = get_vocab(profile)

    end = time.time()
    print("Time to get vocab by source: ", (end - start) / 60, " minutes")

    print("\n|---------------Saving Corpus Stats---------------|\n")

    start = time.time()

    gensim_pars, bert_pars = get_paragraph_stats(profile)

    gen_pars_max = gensim_pars[-1:]
    gen_pars_min = gensim_pars[0]
    gen_pars_5 = len([i for i in gensim_pars if i <= 5])
    bert_pars_max = bert_pars[-1:]
    bert_pars_min = bert_pars[0]
    bert_pars_5 = len([i for i in bert_pars if i <= 5])

    stats_txt = open(join(save_dir, txt_path), "w")

    stats_txt.write("\n\nNumber of documents in corpus: {}".format(profile.shape[0]))
    stats_txt.write("\n\nMax tokens in a document: ")
    stats_txt.write(
        "\n\u2022 Gensim tokenization: {}".format(profile["doc_token_gensim"].max())
    )
    stats_txt.write(
        "\n\u2022 Bert tokenization: {}".format(profile["doc_token_bert"].max())
    )
    stats_txt.write(
        "\n\nMin tokens in a document: {}".format(profile["doc_token_gensim"].min())
    )
    stats_txt.write(
        "\n\u2022 Number empty docs: {}".format(
            profile[profile["doc_token_bert"] == 0].shape[0]
        )
    )
    stats_txt.write("\n\nMean tokens in a document: ")
    stats_txt.write(
        "\n\u2022 Gensim tokenization: {}".format(
            int(round(profile["doc_token_gensim"].mean()))
        )
    )
    stats_txt.write(
        "\n\u2022 Bert tokenization: {}".format(
            int(round(profile["doc_token_bert"].mean()))
        )
    )
    stats_txt.write("\n\nMedian tokens in a document: ")
    stats_txt.write(
        "\n\u2022 Gensim tokenization: {}".format(
            int(round(profile["doc_token_gensim"].median()))
        )
    )
    stats_txt.write(
        "\n\u2022 Bert tokenization: {}".format(
            int(round(profile["doc_token_bert"].median()))
        )
    )
    stats_txt.write("\n\nSTD tokens in a document: ")
    stats_txt.write(
        "\n\u2022 Gensim tokenization: {}".format(
            int(round(profile["doc_token_gensim"].std()))
        )
    )
    stats_txt.write(
        "\n\u2022 Bert tokenization: {}".format(
            int(round(profile["doc_token_bert"].std()))
        )
    )
    stats_txt.write("\n\nUntrimmed vocabulary size: {}".format(full_tokens))
    stats_txt.write(
        "\nTrimmed vocabulary size (stopwords removed): {}".format(full_tokens_stop)
    )
    stats_txt.write("\n\nNumber of paragraphs in corpus: {}".format(len(gensim_pars)))
    stats_txt.write("\n\nMin tokens in a Paragraph: ")
    stats_txt.write("\n\u2022 Gensim tokenization: {}".format(gen_pars_min))
    stats_txt.write("\n\u2022 Bert tokenization: {}".format(bert_pars_min))
    stats_txt.write("\n\nMax tokens in a Paragraph: ")
    stats_txt.write("\n\u2022 Gensim tokenization: {}".format(*gen_pars_max))
    stats_txt.write("\n\u2022 Bert tokenization: {}".format(*bert_pars_max))
    stats_txt.write("\n\nParagraphs with <= 5 tokens: ")
    stats_txt.write("\n\u2022 Gensim tokenization: {}".format(gen_pars_5))
    stats_txt.write("\n\u2022 Bert tokenization: {}".format(bert_pars_5))
    stats_txt.write("\n\nMean tokens per paragraph: ")
    stats_txt.write(
        "\n\u2022 Gensim tokenization: {}".format(int(round(np.mean(gensim_pars))))
    )
    stats_txt.write(
        "\n\u2022 Bert tokenization: {}".format(int(round(np.mean(bert_pars))))
    )
    stats_txt.write("\n\nMedian tokens per paragraph: ")
    stats_txt.write(
        "\n\u2022 Gensim tokenization: {}".format(int(round(np.median(gensim_pars))))
    )
    stats_txt.write(
        "\n\u2022 Bert tokenization: {}".format(int(round(np.median(bert_pars))))
    )
    stats_txt.write("\n\nSTD tokens in paragraphs: ")
    stats_txt.write(
        "\n\u2022 Gensim tokenization: {}".format(int(round(np.std(gensim_pars))))
    )
    stats_txt.write(
        "\n\u2022 Bert tokenization: {}".format(int(round(np.std(bert_pars))))
    )

    stats_txt.close()

    end = time.time()
    print("Time to save stats: ", (end - start) / 60, " minutes")