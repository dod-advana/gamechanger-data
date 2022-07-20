import os
import pandas as pd
from tqdm import tqdm
import requests
import glob
import json
import networkx as nx
import logging
import en_core_web_lg
from collections import Counter
from gamechangerml.src.text_handling.process import preprocess
from gamechangerml import DATA_PATH

logger = logging.getLogger("gamechanger")

nlp = en_core_web_lg.load()


class Rank:
    def train():
        """ train models
            Args:
            Returns:
        """
        pass

    def rerank(self, response: list, alpha: float = 0.85):
        """ rerank function organizes  response using an averaged weighted signal
            Args:
                response: list; search results json with 'docs' field
            Returns:
                same response with additional scores
        """
        documents = response

        if not documents:
            logger.debug("RERANK: response is empty")
            raise ValueError("Empty Response")
        try:
            # print("old ranking")
            # for i in documents:
            #    print(i["id"])
            new_pr = self.get_pagerank(documents, alpha)
            new_pr = self.get_norm_hitcounts(new_pr)
            new_pr = self.avg_scores(new_pr)
            new_pr = sorted(new_pr, key=lambda x: x["r_score"], reverse=True)
            # for debugging
            # print("new ranking")
            # for i in new_pr:
            #    print(i["id"] + " --- Score: " + str(i["r_score"]))
            # print(i["norm_hit_score"])
            return new_pr
        except:
            print("Error could not rerank")
            logger.debug("Could not rerank")
            raise
            return response

    def get_pagerank(self, documents: list, alpha: float = 0.85):
        """ get_pagerank appends pagerank score to document response
            Args:
                documents: LIST of documents with relevant fields
                alpha: damping rate
            Returns:
                new_pr (LIST) same response with additional r_score field
        """
        nodes = []
        edges = []

        for doc in documents:
            doc_type = doc["doc_type"]
            doc_num = doc["doc_num"]
            doc_id = doc_type + " " + doc_num
            nodes.append((doc_id, doc["id"]))

        for doc in documents:
            doc_type = doc["doc_type"]
            doc_num = doc["doc_num"]
            doc_id = doc_type + " " + doc_num
            if "ref_list" in doc:
                ref = list(set([x[0] for x in nodes]) & set(doc["ref_list"]))
                for j in ref:
                    edges.append((doc_id, j))
        # create graph
        G = nx.DiGraph()
        G.add_nodes_from([x[0] for x in nodes])
        G.add_edges_from(edges)
        pr = nx.pagerank(G, alpha)
        pr_sort = {
            k: v for k, v in sorted(pr.items(), key=lambda item: item[1], reverse=True)
        }
        new_pr = []
        # resort based on score for response
        for doc in documents:
            for node in pr_sort:
                doc_id = doc["doc_type"] + " " + doc["doc_num"]
                if doc_id == node:
                    doc["r_score"] = pr_sort[node]
                    new_pr.append(doc)
        return new_pr

    def get_pr_docs(self, directory: str, alpha: float = 0.85):
        """ get_pagerank appends pagerank score to document response
            Args:
                documents: LIST of documents with relevant fields
                alpha: damping rate
            Returns:
                new_pr (LIST) same response with additional r_score field
        """
        nodes = []
        edges = []

        for docpath in tqdm(glob.glob(os.path.join(directory, "*json"))):
            with open(docpath) as f:
                doc = json.load(f)
            doc_type = doc["doc_type"]
            doc_num = doc["doc_num"]
            doc_id = doc_type + " " + doc_num
            nodes.append((doc_id, doc["id"]))

        for docpath in tqdm(glob.glob(os.path.join(directory, "*json"))):
            with open(docpath) as f:
                doc = json.load(f)
            doc_type = doc["doc_type"]
            doc_num = doc["doc_num"]
            doc_id = doc_type + " " + doc_num
            if "ref_list" in doc:
                for ref in doc["ref_list"]:
                    edges.append((doc_id, ref))
        # create graph
        G = nx.DiGraph()
        G.add_nodes_from([x[0] for x in nodes])
        G.add_edges_from(edges)
        pr = nx.pagerank(G, alpha)
        pr_sort = {
            k: v for k, v in sorted(pr.items(), key=lambda item: item[1], reverse=True)
        }
        pr_df = pd.DataFrame.from_dict(pr_sort, orient="index")
        pr_df.reset_index(inplace=True)
        pr_df.rename(columns={"index": "doc_id", 0: "pr"}, inplace=True)
        return pr_df

    def _getCorpusData(self, directory):
        common_orgs = pd.read_csv(os.path.join(
            DATA_PATH,
            "features", "generated_files", "common_orgs.csv"
        ))
        entList = common_orgs.org.to_list()
        corpus_df = pd.DataFrame()

        for docpath in tqdm(glob.glob(os.path.join(directory, "*json"))):
            with open(docpath) as f:
                doc = json.load(f)

            corpus_data = {}
            doc_id = doc["doc_type"] + " " + doc["doc_num"]

            # entities don't support large text
            if len(doc["text"]) > 1000000:
                text = doc["text"][:999999]
            else:
                text = doc["text"]
            ents = nlp(text).ents
            tagged_ents = [{"text": x.text, "label": x.label_} for x in ents]
            tagged_df = pd.DataFrame(tagged_ents)

            if tagged_ents:
                tagged_df = tagged_df[tagged_df.label == "ORG"]
            ent_org_list = []
            for row in tagged_df.itertuples():
                if row.text in entList:
                    ent_org_list.append(row.text)
            counter = Counter(ent_org_list).most_common()

            corpus_data = {
                "id": doc["id"],
                "doc_id": doc_id,
                "keywords": doc["keyw_5"],
                "orgs": dict(counter),
                "text_length": len(preprocess(doc['text'], remove_stopwords=True)) / doc['page_count']
                # "summary": doc["summary_30"],
            }
            corpus_df = corpus_df.append(corpus_data, ignore_index=True)
        # normalize
        corpus_df['text_length'] = (corpus_df['text_length'] - corpus_df['text_length'].min()) / (corpus_df['text_length'].max() - corpus_df['text_length'].min())
        corpus_df['text_length'].loc[corpus_df.text_length == 0] = 0.00001
        return corpus_df

    def get_norm_hitcounts(self, documents: list):
        """ get_norm_hitcounts - hitcounts in both semantic and keyword
            Args: 
                documents: LIST; of documents with relevant fields
            Returns:
                LIST; same response with additional normhitcount field
        """
        newList = []
        # if semantic
        if "relevant_paras" in documents[0]:
            hitCount = [len(x["relevant_paras"]) for x in documents]
            minHit = min(hitCount)
            maxHit = max(hitCount)
            for doc in documents:
                # normalize
                norm = (len(doc["relevant_paras"]) -
                        minHit) / (maxHit - minHit)
                doc["norm_hit_score"] = norm
                newList.append(doc)

        else:
            hitCount = [x["pageHitCount"] for x in documents]
            minHit = min(hitCount)
            maxHit = max(hitCount)
            for doc in documents:
                norm = (doc["pageHitCount"] - minHit) / (maxHit - minHit + 1)
                doc["norm_hit_score"] = norm
                newList.append(doc)

        return newList

    def avg_scores(self, documents: list, weights=[0.3, 0.7]):
        """ avg_scores averages weights for combined score
            Args: 
                documents: LIST of documents with relevant fields
                weights: list or tuple of two weights, first for PR and second for norm hit score
            Returns: 
                LIST of same response with additional r_score field
        """
        newList = []
        for doc in documents:
            doc["r_score"] = (
                (weights[0] * doc["r_score"]) +
                (weights[1] * doc["norm_hit_score"])
            ) / 2
            newList.append(doc)
        return newList
