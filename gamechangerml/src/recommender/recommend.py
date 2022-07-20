import numpy as np
import pandas as pd
import os
import csv
import random
from collections import Counter
import networkx as nx
from typing import List, Dict, Union
from gamechangerml.api.utils.logger import logger
from gamechangerml.src.utilities.user_utils import process_keywords
from gamechangerml import DATA_PATH, REPO_PATH

CORPUS_DIR = os.path.join(REPO_PATH, "gamechangerml", "corpus")
# corpus_list = [i.strip('.json').strip().lstrip() for i in os.listdir(
#    CORPUS_DIR) if os.path.isfile(os.path.join(CORPUS_DIR, i))]
corpus_list = [
    "Title 10",
    "Title 1" "Title 14",
    "DI-MGMT-82160 Base Document 2017-10-02",
    "OPNAVNOTE 5450.4102",
]


def in_corpus(filename: str, corpus_list: List[str]) -> bool:

    if filename in corpus_list:
        return True
    else:
        logger.warning(f"{filename} not found in corpus")
        return False


class Recommender:
    def __init__(self):

        self.graph = self.get_user_graph()

    def get_user_graph(self):
        """Makes graph out of user searches + docs opened"""

        logger.info(" ****    BUILDING RECOMMENDER: Making user graph")
        try:
            user_file = os.path.join(
                DATA_PATH, "user_data", "search_history", "SearchPdfMapping.csv"
            )
            user = pd.read_csv(user_file)
            user = process_keywords(user)
            user.dropna(subset=["document"], inplace=True)
            user["clean_search"] = user["search"].apply(
                lambda x: str(x).replace("&quot;", '"')
            )
            user["clean_doc"] = user["document"].apply(
                lambda x: str(x).replace(",,", ",").strip(".pdf")
            )
            pairs = [(x, y)
                     for y, x in zip(user["clean_doc"], user["clean_search"])]
            user_graph = nx.Graph()
            user_graph.add_edges_from(pairs)

            return user_graph
        except Exception as e:
            logger.warning("Could not make user graph")
            logger.warning(e)
            return nx.Graph()

    def _lookup_history(self, filename: str) -> List[str]:
        """Looks up similar docs by search history"""

        try:
            searches = list(self.graph.adj[filename])
            related = []
            for i in searches:
                rels = list(self.graph.adj[i])
                rels = [x for x in rels if x != filename]
                if rels != []:
                    related.extend(rels)
            logger.info(
                f"Found {len(set(related))} documents opened with same searches"
            )
            related.sort()
            counts = Counter(related)
            top = {
                k: v
                for k, v in sorted(
                    counts.items(), key=lambda item: item[1], reverse=True
                )
            }
            return [f.split(".pdf")[0].strip() for f in list(top.keys())]

        except Exception as e:
            logger.warning("Could not lookup docs from similar searches")
            logger.warning(e)
            return []

    def get_recs(self, sample: bool, limit: int = 5, filenames: list = []):
        """
        Gets similar docs by filename up to the limit.
        When sample=True and filename=None, creates random search for testing.
        """
        if not filenames and sample:
            filename = random.choice(corpus_list)
            logger.info(f" ****    RANDOM SAMPLE: {filename}")

        results = []
        for filename in filenames:
            filename = filename.split(".pdf")[0]
            try:
                g_results = self._lookup_history(filename)
                results = results + g_results[:limit]
            except Exception as e:
                logger.warning(e, exc_info=True)

        return {"filenames": filenames, "results": results}
