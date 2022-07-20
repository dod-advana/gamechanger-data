import os
import pandas as pd
import logging
from datetime import date
from typing import Union
from gamechangerml.api.utils.logger import logger
from gamechangerml.src.featurization.rank_features.generate_ft import generate_ft_doc

logger = logging.getLogger()
S3_DATA_PATH = "bronze/gamechanger/ml-data"

try:
    import wikipedia
except Exception as e:
    logger.warning(e)
    logger.warning("Wikipedia may not be installed")

def make_pop_docs(user_data: pd.DataFrame, save_path: Union[os.PathLike, str]) -> None:
    """Makes popular_documents.csv
    Args: 
        user_data [pd.DataFrame]: df of user search history data
        save_path [str|os.PathLike]: path to save popular docs csv
    """
    logger.info("| --------- Making popular documents csv from user search history ----- |")
    try:
        data = user_data.document.value_counts().to_frame().reset_index()
        data.rename(columns={"document": "pop_score", "index": "doc"}, inplace=True)
        data.to_csv(save_path, index=False)
        logger.info(f" *** Saved popular documents to {save_path}")
    except Exception as e:
        logger.info("Error making popular documents csv")
        logger.info(e)
    return

def make_combined_entities(topics: pd.DataFrame, orgs: pd.DataFrame, save_path: Union[os.PathLike, str]) -> None:
    """Makes combined_entities.csv
    Args:
        topics [pd.DataFrame]: dataframe of topics
        orgs [pd.DataFrame]: dataframe of agencies
        save_path [str|os.PathLike]: path to save the combined entities csv
    Returns:
        None (saves CSV to save_path)
    """
        
    def lookup_wiki_summary(query: str) -> str:
        """Queries the Wikipedia API for summaries
        Args:
            query [str]: query
        Returns:
            [str]: summary / description of query from Wikipedia (if none found, returns an empty string)
        """
        try:
            logger.info(f"Looking up {query}")
            return wikipedia.summary(query).replace("\n", "")
        except Exception as e:
            logger.info(f"Could not retrieve description for {query}")
            logger.info(e)
            return ""

    logger.info("| --------- Making combined entities csv (orgs and topics) -------- |")
    try:
        ## clean up orgs dataframe
        if "Unnamed: 0" in orgs.columns:
            orgs.drop(columns=["Unnamed: 0"], inplace=True)
        orgs.rename(columns={"Agency_Name": "entity_name"}, inplace=True)
        orgs["entity_type"] = "org"
        ## clean up topics dataframe
        topics.rename(
            columns={"name": "entity_name", "type": "entity_type"}, inplace=True
        )    
        combined_ents = orgs.append(topics)
        combined_ents["information"] = combined_ents["entity_name"].apply(
            lambda x: lookup_wiki_summary(x)
        )
        combined_ents["information_source"] = "Wikipedia"
        combined_ents["information_retrieved"] = date.today().strftime(
            "%Y-%m-%d")
        combined_ents.to_csv(save_path, index=False)
        logger.info(f" *** Saved combined entities to {save_path}")
    except Exception as e:
        logger.info("Error making combined entities csv")
        logger.info(e)
    return

def make_corpus_meta(corpus_dir: Union[os.PathLike, str], days: int, prod_data: str) -> None:
    """Generates corpus_meta.csv of ranking features
    Args:
        corpus_dir [str|os.PathLike]: directory of corpus jsons
        days [int]: number of days back to process
        prod_data [str]: filename of prod data
    Returns:
        None (saves corpus_meta.csv file)
    """
    logger.info("| ------------  Making corpus_meta.csv (rank features) ------------- |")
    try:
        generate_ft_doc(corpus_dir, days, prod_data)
    except Exception as e:
        logger.info("Could not generate corpus meta file")
        logger.info(e)