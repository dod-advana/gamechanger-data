import pandas as pd
import ast

df = pd.read_csv(
    "dataScience/src/search/ranking/generated_files/corpus_meta.csv")

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


def get_orgs(docId: str) -> dict:
    if docId in list(df.id):
        return ast.literal_eval(df[df.id == docId].orgs.values[0])
    else:
        return {}


def get_kw_score(docId: str) -> float:
    if docId in list(df.id):
        kw_score = df[df.id == docId].kw_in_doc_score.values[0]
        if pd.isnull(kw_score):
            return rank_min
    else:
        return rank_min

def get_txt_length(docId: str) -> float:
    if docId in list(df.id):
        return df[df.id == docId].text_length.values[0]
    else:
        return rank_min
