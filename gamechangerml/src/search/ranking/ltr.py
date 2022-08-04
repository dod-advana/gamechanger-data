from gamechangerml.src.text_handling.process import preprocess
import numpy as np
import re
import pandas as pd
from tqdm import tqdm
import logging
import os
from elasticsearch import Elasticsearch
import xgboost as xgb
import requests
import json
from sklearn.preprocessing import LabelEncoder
from gamechangerml import MODEL_PATH, DATA_PATH
import typing as t
import base64
from urllib.parse import urljoin
from datetime import datetime, timedelta
from gamechangerml.src.utilities import (
    gc_web_api,
    es_utils,
    user_utils as user,
)


logger = logging.getLogger("gamechanger")

GC_USER_DATA = os.path.join(
    DATA_PATH, "user_data", "search_history", "SearchPdfMapping.csv"
)
LTR_MODEL_PATH = os.path.join(MODEL_PATH, "ltr")
LTR_DATA_PATH = os.path.join(DATA_PATH, "ltr")
os.makedirs(LTR_MODEL_PATH, exist_ok=True)
os.makedirs(LTR_DATA_PATH, exist_ok=True)
gcClient = gc_web_api.GCWebClient()

esu = es_utils.ESUtils()


class LTR:
    def __init__(
        self,
        params={
            "max_depth": 8,
            "eta": 0.3,
            "objective": "rank:pairwise",
        },
    ):
        self.data = self.read_xg_data()
        self.params = params
        self.judgement = None
        self.eval_metrics = [
            "map",
            "map@25",
            "map@50",
            "map@75",
            "map@100",
            "ndcg@1",
            "ndcg@5",
            "ndcg@10",
            "ndcg@20",
            "ndcg@50",
            "ndcg@100",
            "rmse",
            "error",
        ]
        self.mappings = pd.DataFrame()

    def write_model(self, model):
        """write model: writes model to file
        params: model in json form
        returns:
        """
        # write model to json for LTR
        path = os.path.join(LTR_MODEL_PATH, "xgb-model.json")
        with open(path, "w") as output:
            output.write("[" + ",".join(list(model)) + "]")
            output.close()

    def read_xg_data(self, path=os.path.join(LTR_DATA_PATH, "xgboost.csv")):
        """read xg data: reads LTR formatted data
        params: path to file
        returns:
        """
        try:
            df = pd.read_csv(path)
            fts = df[df.columns[5:]]
            fts.index = df.qid

            label = df["ranking"]
            self.data = xgb.DMatrix(fts, label)
            return self.data
        except Exception as e:
            logger.error("LTR - Could not read in data for training")

    def read_mappings(
        self, path=GC_USER_DATA, remote_mappings: bool = False, daysBack: int = 180
    ):
        """read mappings: reads search pdf mappings
        params: path to file
        returns:
            mappings file
        """
        try:
            if remote_mappings:
                self.mappings = self.request_mappings(daysBack)
            else:
                logger.info(
                    "LTR - Not production environment, defaulting to local mappings"
                )
                self.mappings = pd.read_csv(path)
        except Exception as e:
            logger.warning("LTR - Could not request or read mappings")
            logger.warning(e)
        return self.mappings

    def request_mappings(self, daysBack: int = 180):
        mappings = None
        try:
            start_date = (datetime.now() - timedelta(days=daysBack)).replace(
                hour=0, minute=0
            )
            end_date = datetime.now()
            mappings = gcClient.getSearchMappings(
                start_date=start_date, end_date=end_date
            )
            mappings = json.loads(mappings)
            mappings = pd.DataFrame(mappings["data"])
        except Exception as e:
            logger.warning("LTR - Could not request mappings from GC Web")
        return mappings

    def train(self, data=None, params=None, write=True):
        """train - train a xgboost model with parameters
        params:
            write: boolean to write to file
        returns:
            bst: xgboost object
            model: model json
        """
        if not data:
            data = self.data
        if not params:
            params = self.params
        bst = xgb.train(params, data)
        cv = xgb.cv(params, dtrain=data, nfold=3, metrics=self.eval_metrics)
        model = bst.get_dump(
            fmap=os.path.join(LTR_DATA_PATH, "featmap.txt"), dump_format="json"
        )
        if write:
            self.write_model(model)
            path = os.path.join(LTR_MODEL_PATH, "ltr_evals.csv")
            cv.to_csv(path, index=False)
        return bst, model

    def post_model(self, model, model_name):
        """post model - post a model to ES
        params:
            model: model in json form
            model_name: model name for ES
        returns:
            r: results
        """
        query = {
            "model": {
                "name": model_name,
                "model": {"type": "model/xgboost+json", "definition": model},
            }
        }
        endpoint = "/_ltr/_featureset/doc_features/_createmodel"
        r = esu.post(endpoint, data=json.dumps(query))
        return r.content

    def search(self, terms, rescore=True):
        """search: searches with a rescore with ltr option
        params:
            terms: search terms
            rescore: boolean
        returns:
            r: results
        """
        query = {
            "_source": {"includes": ["pagerank_r", "kw_doc_score_r"]},
            "stored_fields": ["filename", "title"],
            "from": 0,
            "size": 15,
            "query": {
                "bool": {
                    "must": [],
                    "should": [
                        {
                            "nested": {
                                "path": "paragraphs",
                                "inner_hits": {},
                                "query": {
                                    "bool": {
                                        "should": [
                                            {
                                                "query_string": {
                                                    "query": f"{terms}",
                                                    "default_field": "paragraphs.par_raw_text_t.gc_english",
                                                    "default_operator": "AND",
                                                    "fuzzy_max_expansions": 1000,
                                                    "fuzziness": "AUTO",
                                                    "analyzer": "gc_english",
                                                }
                                            }
                                        ]
                                    }
                                },
                            }
                        },
                        {
                            "multi_match": {
                                "query": f"{terms}",
                                "fields": ["display_title_s.search"],
                                "type": "phrase",
                                "operator": "and",
                                "boost": 4,
                            }
                        },
                        {"wildcard": {"keyw_5": {"value": f"*{terms}*"}}},
                        {
                            "wildcard": {
                                "display_title_s.search": {
                                    "value": f"*{terms}*",
                                    "boost": 6,
                                }
                            }
                        },
                    ],
                    "minimum_should_match": 1,
                    "filter": [{"term": {"is_revoked_b": "false"}}],
                }
            },
            "highlight": {
                "fields": {"display_title_s.search": {}, "keyw_5": {}, "id": {}},
                "fragmenter": "simple",
            },
            "sort": [{"_score": {"order": "desc"}}],
        }
        if rescore:
            query["rescore"] = {
                "query": {
                    "rescore_query": {
                        "sltr": {
                            "params": {"keywords": f"{terms}"},
                            "model": "lambda_rank1",
                        }
                    }
                }
            }
        r = esu.client.search(index=esu.es_index, body=dict(query))
        return r

    def generate_judgement(self, remote_mappings: bool = False, daysBack: int = 180):
        """generate judgement - generates judgement list from user mapping data
        params:
            mappings: dataframe of user data extracted from pdf mapping table
        returns:
            count_df: cleaned dataframe with search mapped data
        """
        self.read_mappings(remote_mappings=remote_mappings, daysBack=daysBack)
        mapped_keywords = user.process_keywords(self.mappings)
        ranked_docs = user.rank_docs(mapped_keywords)
        self.judgement = ranked_docs

        return ranked_docs

    def query_es_fts(self, df):
        """query ES features: gets ES feature logs from judgement list
        params:
            df: dataframe of judgement list and keyword
        returns:
            ltr_log: logs of from ES
        """
        ltr_log = []
        logger.info("LTR - Querying ES LTR logs")
        # loop through all unique keywords
        query_list = []
        for kw in tqdm(df.keyword.unique()):
            # get frame of all of the keyword rows
            tmp = df[df.keyword == kw]
            # get logged feature

            for docs in tmp.itertuples():
                doc = docs.Index
                q = self.construct_query(doc, kw)
                query_list.append(json.dumps({"index": esu.es_index}))
                query_list.append(json.dumps(q))
        query = "\n".join(query_list)
        res = esu.client.msearch(body=query)
        ltr_log = [x["hits"]["hits"] for x in res["responses"]]
        return ltr_log

    def process_ltr_log(self, ltr_log, num_fts=8):
        """process ltr log: extracts features from ES logs for judgement list
        params:
            ltr_log: results from ES
            num_fts: number of features
        returns:
            all_vals: all logged features in matrix
        """
        all_vals = []
        logger.info("LTR - processing logs")
        for entries in ltr_log:
            if len(entries) > 0:
                # loop through entry logs (num of features)
                fts = []
                for entry in entries[0]["fields"]["_ltrlog"][0]["log_entry1"]:
                    # checks if entry is empty
                    if "value" in entry:
                        fts.append(entry["value"])
                    else:
                        fts.append(0)
                all_vals.append(fts)
            # if the doc doesnt exist then add all 0s
            else:
                all_vals.append(np.zeros(num_fts))
        return all_vals

    def generate_ft_txt_file(self, df):
        """generate feature text file: creates the LTR formatted training data
        params:
            df: dataframe of the judgement list with features
        returns:
            outputs a file
        """
        try:
            ltr_log = self.query_es_fts(df)
            vals = self.process_ltr_log(ltr_log)
            ft_df = pd.DataFrame(
                vals,
                columns=[
                    "title",
                    "keyw_5",
                    "topics",
                    "entities",
                    "textlength",
                    "paragraph",
                    "popscore",
                    "paragraph-phrase",
                ],
            )
            df.reset_index(inplace=True)
            df = pd.concat([df, ft_df], axis=1)

            logger.info("LTR - Generating csv file")
            df.to_csv(os.path.join(LTR_DATA_PATH, "xgboost.csv"), index=False)
        except Exception as e:
            logger.error(e)
            logger.info("LTR - Failed in generating feature text file")
        return df

    def construct_query(self, doc, kw):
        """construct query: constructs query for logging features from es
        params:
            doc: document name that is in corpus
            kw: keyword to search on
        returns: query
        """
        query = {
            "_source": ["filename", "fields"],
            "query": {
                "bool": {
                    "filter": [
                        {"terms": {"filename": [doc]}},
                        {
                            "sltr": {
                                "_name": "logged_featureset",
                                "featureset": "doc_features",
                                "params": {"keywords": kw},
                            }
                        },
                    ]
                }
            },
            "ext": {
                "ltr_log": {
                    "log_specs": {
                        "name": "log_entry1",
                        "named_query": "logged_featureset",
                    }
                }
            },
        }
        return query

    def post_features(self):
        """post features: post features to es"""
        query = {
            "featureset": {
                "name": "doc_features",
                "features": [
                    {
                        "name": "title",
                        "params": ["keywords"],
                        "template_language": "mustache",
                        "template": {
                            "wildcard": {
                                "display_title_s.search": {
                                    "value": "*{{keywords}}*",
                                    "boost": 2,
                                }
                            }
                        },
                    },
                    {
                        "name": "keyw_5",
                        "params": ["keywords"],
                        "template_language": "mustache",
                        "template": {"match": {"keyw_5": "{{keywords}}"}},
                    },
                    {
                        "name": "topics",
                        "params": ["keywords"],
                        "template_language": "mustache",
                        "template": {"match": {"topics_s": "{{keywords}}"}},
                    },
                    {
                        "name": "entities",
                        "params": ["keywords"],
                        "template_language": "mustache",
                        "template": {"match": {"top_entities_t": "{{keywords}}"}},
                    },
                    {
                        "name": "textlength",
                        "params": ["keywords"],
                        "template_language": "mustache",
                        "template": {
                            "function_score": {
                                "functions": [
                                    {
                                        "field_value_factor": {
                                            "field": "page_count",
                                            "missing": 0,
                                        }
                                    }
                                ],
                                "query": {"match_all": {}},
                            }
                        },
                    },
                    {
                        "name": "paragraph",
                        "params": ["keywords"],
                        "template_language": "mustache",
                        "template": {
                            "nested": {
                                "path": "paragraphs",
                                "inner_hits": {},
                                "query": {
                                    "bool": {
                                        "should": [
                                            {
                                                "query_string": {
                                                    "query": "{{keywords}}",
                                                    "default_field": "paragraphs.par_raw_text_t.gc_english",
                                                    "default_operator": "AND",
                                                    "fuzzy_max_expansions": 1000,
                                                    "fuzziness": "AUTO",
                                                    "analyzer": "gc_english",
                                                }
                                            }
                                        ]
                                    }
                                },
                            }
                        },
                    },
                    {
                        "name": "popscore",
                        "params": ["keywords"],
                        "template_language": "mustache",
                        "template": {
                            "function_score": {
                                "functions": [
                                    {
                                        "field_value_factor": {
                                            "field": "pop_score",
                                            "missing": 0,
                                        }
                                    }
                                ],
                                "query": {"match_all": {}},
                            }
                        },
                    },
                    {
                        "name": "paragraph-phrase",
                        "params": ["keywords"],
                        "template_language": "mustache",
                        "template": {
                            "nested": {
                                "path": "paragraphs",
                                "inner_hits": {},
                                "query": {
                                    "bool": {
                                        "should": [
                                            {
                                                "match_phrase": {
                                                    "paragraphs.par_raw_text_t.gc_english": "{{keywords}}"
                                                }
                                            }
                                        ]
                                    }
                                },
                            }
                        },
                    },
                ],
            }
        }
        endpoint = "/_ltr/_featureset/doc_features"
        r = esu.post(endpoint, data=json.dumps(query))
        return r.content

    def post_init_ltr(self):
        endpoint = "/_ltr"
        r = esu.put(endpoint)
        return r.content

    def delete_ltr(self, model_name="ltr_model"):
        endpoint = f"/_ltr/_model/{model_name}"
        r = esu.delete(endpoint)
        return r.content
