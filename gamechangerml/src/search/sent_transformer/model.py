from txtai.embeddings import Embeddings
from txtai.pipeline import Similarity
from txtai.ann import ANN

import os
import numpy as np
import pandas as pd
import pickle
import torch
import time
import threading

from gamechangerml.src.text_handling.corpus import LocalCorpus
from gamechangerml.api.utils import processmanager
from gamechangerml.api.utils.logger import logger
from gamechangerml.src.utilities.test_utils import *
from gamechangerml.src.text_handling.process import preprocess
from gamechangerml.api.utils.pathselect import get_model_paths
from gamechangerml.src.model_testing.validation_data import MSMarcoData
from gamechangerml.configs.config import EmbedderConfig


class SentenceEncoder(object):
    """
    Handles text encoding and creating of ANNOY index
    for the initial search

    Args:
        encoder_model (str): Model name supported by huggingface
            and txtai to generate the document embeddings
        use_gpu (bool): Boolean to check if a GPU would be used
    """

    def __init__(
        self,
        encoder_model_name,
        min_token_len,
        return_id,
        verbose,
        transformer_path,
        model=None,
        use_gpu=False,
        bert_tokenize=False,
    ):

        if model:
            self.encoder_model = model
        else:
            self.encoder_model = os.path.join(transformer_path, encoder_model_name)
        self.bert_tokenizer = None
        if bert_tokenize:
            self.bert_tokenizer = self.encoder_model
        self.min_token_len = min_token_len
        self.return_id = return_id
        self.verbose = verbose

        if use_gpu and torch.cuda.is_available():
            self.use_gpu = use_gpu
        else:
            self.use_gpu = False

        self.embedder = Embeddings(
            {"method": "transformers", "path": self.encoder_model, "gpu": self.use_gpu}
        )

    def _index(self, corpus, index_path, overwrite=False, save_embedding=False):
        """
        Builds an embeddings index.
        Args:
            corpus: list of (id, text|tokens, tags)
            index_path: Path of where to store and reference
                existing index
            overwrite: Boolean check to predict whether if an
                existing index will be overwritten
        """
        # Transform documents to embeddings vectors
        logger.info("Getting ids, dimensions, stream")
        ids, dimensions, stream = self.embedder.model.index(corpus)

        logger.info("Loading embeddings into memory")
        # Load streamed embeddings back to memory
        embeddings = np.empty((len(ids), dimensions), dtype=np.float32)
        with open(stream, "rb") as queue:
            for x in range(embeddings.shape[0]):
                embeddings[x] = pickle.load(queue)

        # Remove temporary file
        logger.info("Removing temporary file")
        os.remove(stream)
        logger.info("Making dataframe")
        all_text = []
        for para_id, text, _ in corpus:
            all_text.append([text, para_id])

        df = pd.DataFrame(all_text, columns=["text", "paragraph_id"])

        embedding_path = os.path.join(index_path, "embeddings.npy")
        dataframe_path = os.path.join(index_path, "data.csv")
        ids_path = os.path.join(index_path, "doc_ids.txt")

        """
        # Load new data
        if os.path.isfile(embedding_path) and (overwrite is False):
            logger.info(f"Loading new data from {embedding_path}")

            # Load existing embeddings
            old_embeddings = np.load(embedding_path)  # LOAD EMBEDDINGS
            # Remove embeddings with document id overlaps
            embeddings = np.vstack((old_embeddings, embeddings))

            # load IDs
            old_ids = [doc_id[:-1] for doc_id in open_txt(ids_path)]
            logger.debug(f"New ID Length = {len(ids)}")
            logger.debug(f"Old ID Length = {len(old_ids)}")
            # Remove document ids overlaps
            logger.debug(f"New ID Length = {len(ids)}")
            ids = old_ids + ids
            logger.debug(f"Merged  ID Length = {len(ids)}")

            # Append new dataframe
            old_df = pd.read_csv(dataframe_path)
            df = pd.concat([old_df, df])
        """

        # Store embeddings and document index
        # for future reference
        if save_embedding:
            np.save(embedding_path, embeddings)
        with open(ids_path, "w") as fp:
            fp.writelines([i + "\n" for i in ids])

        # Save data csv
        logger.info(f"Saving data.csv to {str(dataframe_path)}")
        df.to_csv(dataframe_path, index=False)

        # Normalize embeddings
        self.embedder.normalize(embeddings)

        # Save embeddings metadata
        self.embedder.config["ids"] = ids
        self.embedder.config["dimensions"] = dimensions

        # Create embeddings index
        logger.info(f"Creating embeddings and index")
        self.embedder.embeddings = ANN.create(self.embedder.config)
        logger.info(f"Created embeddings")

        # Build the index
        self.embedder.embeddings.index(embeddings)
        logger.info(f"Built the embeddings index")

    def index_documents(self, corpus_path, index_path, files_to_use=None):
        """
        Create the index and accompanying dataframe to perform text
        and paragraph id search
        Args:
            corpus_path (str): Folder path containing JSON files having
                GAMECHANGER format
            index_path (str): Folder path to where the index of the document
                would be storred
        """
        logger.info(f"Indexing documents from {corpus_path}")

        if corpus_path:
            corp = LocalCorpus(
                corpus_path,
                return_id=self.return_id,
                min_token_len=self.min_token_len,
                verbose=self.verbose,
                bert_based_tokenizer=self.bert_tokenizer,
                files_to_use=files_to_use,
            )
            corpus = [(para_id, " ".join(tokens), None) for tokens, para_id in corp]
            logger.info(
                f"\nLength of batch (in par ids) for indexing : {str(len(corpus))}"
            )

        else:
            logger.info(
                "Did not include path to corpus, making test index with msmarco data"
            )
            data = MSMarcoData()
            corpus = data.corpus

        processmanager.update_status(
            processmanager.training,
            0,
            1,
            "building sent index",
            thread_id=threading.current_thread().ident,
        )

        self._index(corpus, index_path)
        processmanager.update_status(
            processmanager.training,
            1,
            1,
            "finished building sent index",
            thread_id=threading.current_thread().ident,
        )

        self.embedder.save(index_path)
        logger.info(f"Saved embedder to {index_path}")


class SimilarityRanker(object):
    def __init__(self, sim_model_name, transformer_path):

        self.sim_model = os.path.join(transformer_path, sim_model_name)
        self.similarity = Similarity(self.sim_model)

    def re_rank(self, query, top_docs):
        results = []
        texts = [x["text"] for x in top_docs]
        scores = self.similarity(query, texts)
        for idx, score in scores:
            doc = {}
            doc["score"] = score
            doc["id"] = top_docs[idx]["id"]
            doc["text"] = top_docs[idx]["text"]
            results.append(doc)
        return results


class SentenceSearcher(object):
    """
    Imports the text index generated by the SentenceEncoder and
    performs the search functionality. Initial set of documents
    are first retrieved through an Annoy index then reranked with
    the similarity model.

    Args:
        index_path (str): Path to index directory generated by the
            SentenceEncoder
        encoder_model (str): Model name supported by huggingface
            and txtai to generate the document embeddings
        sim_model (str): Model name supported by huggingface
            and txtai to calculate similarity between query and document
    """

    def __init__(self, sim_model_name, index_path, transformer_path, sim_model=None):

        self.embedder = Embeddings()
        self.embedder.load(index_path)
        # replace this with looking up ES
        self.data = pd.read_csv(
            os.path.join(index_path, "data.csv"), dtype={"paragraph_id": str}
        )
        try:
            silver_eval_file = get_most_recent_eval(
                os.path.join(index_path, "evals_gc", "silver")
            )
            silver_eval = open_json(
                silver_eval_file, os.path.join(index_path, "evals_gc", "silver")
            )
            self.auto_threshold = EmbedderConfig.THRESHOLD_MULTIPLIER * float(
                silver_eval["best_threshold"]
            )
            logger.info(f"Setting automatic cutoff score to {self.auto_threshold}")
        except Exception as e:
            logger.error(
                f"Do not have best threshold available in eval data, defaulting to {EmbedderConfig.DEFAULT_THRESHOLD}"
            )
            self.auto_threshold = EmbedderConfig.DEFAULT_THRESHOLD
        if sim_model:
            self.similarity = sim_model
        else:
            self.similarity = SimilarityRanker(sim_model_name, transformer_path)

    def retrieve_topn(self, query, num_results=10):
        retrieved = self.embedder.search(query, limit=num_results)
        results = []
        for doc_id, score in retrieved:
            doc = {}
            text = self.data[self.data["paragraph_id"] == str(doc_id)].iloc[0]["text"]
            doc["id"] = doc_id
            doc["text"] = text
            doc["text_length"] = len(text)
            doc["score"] = score
            results.append(doc)
        return results

    def search(
        self, query, num_results=10, process=False, externalSim=True, threshold="auto"
    ):
        """
        Search the index and perform a similarity scoring reranker at
        the topn returned documents
        Args:
            query (str): Query text to search in documents
        Returns:
            rerank (list): List of tuples following a (score, paragraph_id,
                paragraph_text) format ranked based on similarity with query
        """
        if process:
            query = " ".join(preprocess(query))
        if threshold == "auto":
            cutoff_score = self.auto_threshold
        else:
            try:
                threshold = float(threshold)
                if (
                    threshold < 1 and threshold > 0
                ):  # if a threshold is manually set betweeen 0-1, use that
                    cutoff_score = threshold
                    logger.info(f"Manually setting threshold to {threshold}")
            except:
                cutoff_score = self.auto_threshold

        logger.info(f"Sentence searching for: {query}")
        if len(query) > 2:
            top_results = self.retrieve_topn(query, num_results)
            # choose to use an external similarity transformer
            if externalSim:
                return self.similarity.re_rank(query, top_results)
            else:
                # adding normalize text length to score and sorting
                finalResults = []
                result_text = [len(x["text"]) for x in top_results]
                length_scores = np.interp(
                    result_text, (min(result_text), max(result_text)), (0, 0.2)
                )
                for idx, doc in enumerate(top_results):
                    doc["text_length"] = length_scores[idx]
                    doc["score"] = doc["score"]
                    if doc["score"] >= cutoff_score:
                        doc["passing_result"] = 1
                    else:
                        doc["passing_result"] = 0
                    finalResults.append(doc)
                finalResults = sorted(
                    finalResults, key=lambda i: i["score"], reverse=True
                )

                return finalResults
        else:
            return []
