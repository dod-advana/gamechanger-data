import psycopg2 as ps
import pandas as pd
import re
from gamechangerml.src.text_handling.process import preprocess
from collections import Counter
import logging
from tqdm import tqdm
import os

logger = logging.getLogger("gamechanger")

PG_USER = "postgres"
PG_PASS = "password"
PG_HOST = os.environ.get('PG_HOST', 'localhost')
PG_PORT = 5432
PG_DB = "uot"


def ps_connect():
    """ postgres open connect
    Args:
    Returns:
        postgres connection object
    """
    conn = ps.connect(
        user=PG_USER, password=PG_PASS, host=PG_HOST, port=PG_PORT, database=PG_DB
    )
    return conn


def get_searchLogs(from_date: str):
    """ get searchlogs
    Args:
        from_date: get logs from certain date FORMAT '2020-08-20'
    Returns:
        json response from query
    """
    conn = ps_connect()
    cursor = conn.cursor()
    query = f"SELECT * FROM gc_history WHERE run_at >= '{from_date}'::date ORDER BY run_at DESC"
    cursor.execute(query)
    resp = cursor.fetchall()
    return resp

def get_entities():
    conn = ps_connect()
    cursor = conn.cursor()
    query = f"SELECT * FROM gc_entities"
    cursor.execute(query)
    resp = cursor.fetchall()
    return resp



def get_annotationLogs(from_date: str):
    # doesn't exist yet
    conn = ps_connect()
    cursor = conn.cursor()
    query = f"SELECT * FROM gc_annotations WHERE run_at >= '{from_date}'::date ORDER BY run_at DESC"
    cursor.execute(query)
    resp = cursor.fetchall()
    return resp


def _logs_toDf(searchLog: list):
    df = pd.DataFrame(
        searchLog,
        columns=[
            "temp_index",
            "user_hash",
            "search",
            "run_at",
            "completion_time",
            "num_results",
            "had_error",
            "is_semantic_search",
        ],
    )
    df.drop(columns=["temp_index"], inplace=True)
    df = process_search_terms(df)
    return df


def get_top_keywords(search_df: pd.DataFrame()):
    """ get top keywords frm searchlogs
    Args:
        searchLog: LIST requests response from postgres 
    Returns:
        dataframe of top words and counts
    """
    cnt = Counter()
    ignore_words = ["artificial intelligence president"]
    for log in tqdm(search_df.itertuples()):
        split_word = re.split(" AND | OR", log.search, flags=re.IGNORECASE)
        for terms in split_word:
            terms = _preprocess_str(terms)
            if len(terms) > 0:
                if terms not in ignore_words:
                    cnt[terms] += 1

    df = pd.DataFrame(columns=["keywords", "amt"], data=cnt.items())
    df = score_popularity(df)
    df.sort_values(["pop_score"], ascending=False, inplace=True)
    return df


def scored_logs(search_logs) -> pd.DataFrame:
    """ gets top keywords and appends score to all cleaned search data 
        Args:
            search_logs:
        Returns:
            dataframe with pop_score column
    """
    if type(search_logs) == list:
        logger.info("Search logs is a list")
        try:
            search_df = _logs_toDf(search_logs)
        except Exception as e:
            logger.info("Could not make search df")
            logger.info(e)
    elif type(search_logs) == pd.DataFrame:
        logger.info("Search logs is a dataframe")
        try:
            search_df = process_search_terms(search_logs)
        except Exception as e:
            logger.info("Could not make search df")
            logger.info(e)
    else:
        logger.error("Wrong type for search logs")
        return
    
    try:
        top_kw = get_top_keywords(search_df)
    except Exception as e:
            logger.info("Could not get top keywords")
            logger.info(e)
    try:
        for row in tqdm(top_kw.itertuples()):
            search_df.loc[search_df.search ==
                        row.keywords, "pop_score"] = row.pop_score
    except Exception as e:
            logger.info("Could not set row pop scores")
            logger.info(e)
    return search_df


def process_search_terms(df: pd.DataFrame) -> pd.DataFrame:
    """ process_search_terms cleans the search key words column
        Args:
            df: dataframe of all search data
        Returns:
            dataframe with cleaned search terms
    """
    df.search = df.search.replace('"', "", regex=True)
    df.search = df.search.replace("'", "", regex=True)
    df.search = df.search.apply(_preprocess_str)
    df = df[df.search != ""]
    return df


def _preprocess_str(terms: list) -> str:
    """ preprocess back to string """
    words = preprocess(terms)
    return " ".join(words)


def score_popularity(df: pd.DataFrame) -> pd.DataFrame:
    """ scores the popularity 
        Args:
            df: dataframe of data
        Returns:
            Dataframe
    """
    df["pop_score"] = (df.amt - df.amt.min()) / df.amt.max()
    return df
