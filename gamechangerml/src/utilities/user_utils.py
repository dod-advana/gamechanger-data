import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder
import re
from gamechangerml.src.text_handling.process import preprocess
from tqdm import tqdm


def normalize(arr, start=0, end=4):
    """normalize: basic normalize between two numbers function
    params:
        arr: array to normalize
        start: beginning number integer
        end: ending number integer
    returns: normalized array
    """
    arr = np.log(arr)
    width = end - start
    res = (arr - arr.min()) / (arr.max() - arr.min()) * width + start
    return res


def process_keywords(searches: pd.DataFrame, multiplier: int = 2):
    """
    process_keywords - processes a user search and actions dataframe
    params:
        searches - dataframe of user DataFrame
        multiplier - multiplies specific actions like export to weigh more
    output:
        tuple_df - a cleaned and processed keyword dataframe
    """
    searches.value = searches.value.ffill(axis=0)
    searches.value.replace("&quot;", "", regex=True, inplace=True)
    # multiple the factor of these types of actions for ranking
    export_df = searches[searches.action == "ExportDocument"]
    for i in range(0, multiplier):
        export_df = export_df.append(export_df)
    favorite_df = searches[searches.action == "Favorite"]
    for i in range(0, multiplier):
        favorite_df = favorite_df.append(favorite_df)
    searches = searches.append(favorite_df)
    searches = searches.append(export_df)
    word_tuples = []
    for row in tqdm(searches.itertuples()):
        words = row.value.split(" ")
        clean_phr = re.sub(r"[^\w\s]", "", row.value)
        clean_phr = preprocess(clean_phr, remove_stopwords=True)
        if clean_phr:
            word_tuples.append((" ".join(clean_phr), row.document))

        for word in words:
            clean = word.lower()
            clean = re.sub(r"[^\w\s]", "", clean)
            clean = preprocess(clean, remove_stopwords=True)
            if clean:
                tup = (clean[0], row.document)
                word_tuples.append(tup)
    tuple_df = pd.DataFrame(word_tuples, columns=["search", "document"])
    return tuple_df


def rank_docs(tuple_df: pd.DataFrame):
    """
    rank_docs - ranks documents by keyword count for judgement list
    params:
        tuple_df - processed dataframe from proess_keywords
    output:
        count_df - ranked and counts of keywords in dataframe
    """

    count_df = pd.DataFrame()
    for keyword in tqdm(tuple_df.search.unique()):
        a = tuple_df[tuple_df.search == keyword]
        tmp_df = a.groupby("document").count()
        tmp_df["keyword"] = keyword
        count_df = count_df.append(tmp_df)
    count_df.sort_values("search")
    arr = count_df.search.copy()
    count_df["ranking"] = normalize(arr)
    count_df.ranking = count_df.ranking.apply(np.ceil)
    count_df.ranking = count_df.ranking.astype(int)
    le = LabelEncoder()
    count_df["qid"] = le.fit_transform(count_df.keyword)
    return count_df
