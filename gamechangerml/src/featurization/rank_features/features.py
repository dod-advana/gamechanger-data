import pandas as pd
import ast
from gamechangerml import DATA_PATH
import os

df = pd.read_csv(os.path.join(DATA_PATH, "features/generated_files/corpus_meta.csv"))
pop_df = pd.read_csv(os.path.join(DATA_PATH, "features/popular_documents.csv"))


""" retrieve pre-generated features from corpus
    - pr: pagerank
    - orgs: organization importance
    - kw_in_doc_score: keyword in doc score historically 
"""
df.orgs.replace({"'": '"'}, regex=True, inplace=True)

rank_min = 0.00001


def get_pr(docId: str) -> float:
    if docId in list(df.id):
        return df[df.id == docId].pr.values[0]
    else:
        return rank_min


def get_pop_score(docId: str) -> float:
    if docId in list(pop_df.doc):
        return float(pop_df[pop_df.doc == docId].pop_score.values[0])
    else:
        return 0.0