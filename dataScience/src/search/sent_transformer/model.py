from txtai.embeddings import Embeddings
from txtai.pipeline import Similarity
from txtai.ann import ANN

import os
import json
import numpy as np
import pandas as pd

import logging
import pickle

from dataScience.src.text_handling.corpus import LocalCorpus, SentCorpus

import torch

from tqdm import tqdm

logger = logging.getLogger(__name__)


class SentenceEncoder(object):
    """
    Handles text encoding and creating of ANNOY index
    for the initial search

    Args:
        encoder_model (str): Model name supported by huggingface
            and txtai to generate the document embeddings
        use_gpu (bool): Boolean to check if a GPU would be used
    """

    def __init__(self, encoder_model=None, use_gpu=False):

        if encoder_model:
            self.encoder_model = encoder_model
        else:
            self.encoder_model = "sentence-transformers/msmarco-distilbert-base-v2"

        if use_gpu and torch.cuda.is_available():
            self.use_gpu = use_gpu
        else:
            self.use_gpu = False

        self.embedder = Embeddings(
            {"method": "transformers", "path": self.encoder_model, "gpu": self.use_gpu}
        )

        self.mapper = {}

    def _index(self, corpus, index_path, overwrite=False):
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
        ids, dimensions, stream = self.embedder.model.index(corpus)

        # Load streamed embeddings back to memory
        embeddings = np.empty((len(ids), dimensions), dtype=np.float32)
        with open(stream, "rb") as queue:
            for x in range(embeddings.shape[0]):
                embeddings[x] = pickle.load(queue)

        # Remove temporary file
        os.remove(stream)

        all_text = []
        for para_id, text, _ in corpus:
            all_text.append([text, para_id])

        df = pd.DataFrame(all_text, columns=["text", "paragraph_id"])

        embedding_path = os.path.join(index_path, "embeddings.npy")
        dataframe_path = os.path.join(index_path, "data.csv")
        ids_path = os.path.join(index_path, "doc_ids.txt")

        # Load new data
        if os.path.isfile(embedding_path) and (overwrite is False):
            old_embed_path = os.path.join(index_path, "embeddings.npy")
            old_dataframe_path = os.path.join(index_path, "data.csv")
            old_ids_path = os.path.join(index_path, "doc_ids.txt")
            # Load existing embeddings
            old_embeddings = np.load(old_embed_path)  # LOAD EMBEDDINGS
            with open(old_ids_path, "r") as fp:
                old_ids = fp.readlines()
                old_ids = [doc_id[:-1] for doc_id in old_ids]

            # Remove embeddings with document id overlaps
            embeddings = np.vstack((old_embeddings, embeddings))

            # Append new dataframe
            old_df = pd.read_csv(old_dataframe_path)
            df = pd.concat([old_df, df])

            logger.debug(f"New ID Length = {len(ids)}")
            logger.debug(f"Old ID Length = {len(old_ids)}")
            # Remove document ids overlaps
            logger.debug(f"New ID Length = {len(ids)}")
            ids = old_ids + ids
            logger.debug(f"Merged  ID Length = {len(ids)}")

        # Store embeddings and document index
        # for future reference
        np.save(embedding_path, embeddings)
        with open(ids_path, "w") as fp:
            fp.writelines([i + "\n" for i in ids])

        # Save data csv
        csv_path = os.path.join(index_path, "data.csv")
        df.to_csv(csv_path, index=False)

        # Normalize embeddings
        self.embedder.normalize(embeddings)

        # Save embeddings metadata
        self.embedder.config["ids"] = ids
        self.embedder.config["dimensions"] = dimensions

        # Create embeddings index
        self.embedder.embeddings = ANN.create(self.embedder.config)

        # Build the index
        self.embedder.embeddings.index(embeddings)

        # Save id mapper to JSON
        with open(os.path.join(index_path, "mapper.json"), "w") as fp:
            json.dump(self.mapper, fp)


    def index_documents(
        self, corpus_path, index_path, min_token_len=10, overwrite=False, new_parser = False
    ):
        """
        Create the index and accompanying dataframe to perform text
        and paragraph id search
        Args:
            corpus_path (str): Folder path containing JSON files having
                GAMECHANGER format
            index_path (str): Folder path to where the index of the document
                would be storred
        """
        logging.info(f"Indexing documents from {corpus_path}")

        if new_parser:
            corp = SentCorpus(
                corpus_path, return_id=True, min_token_len=min_token_len, verbose=True
            )

            for _, para_id, old_id in corp:
                self.mapper[para_id] = old_id

            self._index(
                [(para_id, " ".join(tokens), None) for tokens, para_id, old_id in corp],
                index_path,
                overwrite=overwrite,
            )

        else:
            corp = LocalCorpus(
                corpus_path, return_id=True, min_token_len=min_token_len, verbose=True
            )
            self._index(
                [(para_id, " ".join(tokens), None) for tokens, para_id in corp],
                index_path,
                overwrite=overwrite,
            )

        self.embedder.save(index_path)

    def new_index_documents(
        self, new_sent_corpus, old_sent_corpus, index_path, min_token_len=10, overwrite=False, new_parser = False
    ):
        """
        This is a rough approach for index two corpuses with
        different parsing approaches. new_sent_corpus is for
        the directory that contains the new sentence parsing approach
        while old_sent_corpus contains the old approach.
        """
        logging.info(f"Indexing documents from {new_sent_corpus}")

        print("Getting Sentence Corpus")
        new_corp = SentCorpus(new_sent_corpus, return_id = True, min_token_len = min_token_len)
        new_corp = [(para_id, " ".join(tokens), None) for tokens, para_id, old_id in tqdm(new_corp)]
        
        print("Getting Old Corpus")
        old_corp = LocalCorpus(old_sent_corpus, return_id = True, min_token_len = min_token_len)
        old_corp = [(para_id, " ".join(tokens), None) for tokens, para_id in tqdm(old_corp) if not para_id.lower().startswith("dod")]

        corp = old_corp + new_corp

        print("Indexing")
        self._index(
            tqdm(corp),
            index_path,
            overwrite = overwrite
        )

        self.embedder.save(index_path)


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

    def __init__(self, index_path, sim_model=None):

        if sim_model:
            self.sim_model = sim_model
        else:
            self.sim_model = "valhalla/distilbart-mnli-12-3"

        self.embedder = Embeddings()
        self.embedder.load(index_path)
        self.similarity = Similarity(self.sim_model)
        self.data = pd.read_csv(os.path.join(index_path, "data.csv"))

    def search(self, query, n_returns=10):
        """
        Search the index and perform a similarity scoring reranker at
        the topn returned documents
        Args:
            query (str): Query text to search in documents
            n_returns (int): Number of documents to return

        Returns:
            rerank (list): List of tuples following a (score, paragraph_id,
                paragraph_text) format ranked based on similarity with query
        """
        retrieved = self.embedder.search(query, limit=n_returns)
        doc_ids = []
        doc_texts = []
        for doc_id, score in retrieved:
            doc_ids.append(doc_id)
            text = self.data[self.data["paragraph_id"]
                             == doc_id].iloc[0]["text"]
            doc_texts.append(text)

        results = []
        for idx, score in self.similarity(query, doc_texts):
            doc = {}
            doc["score"] = score
            doc["id"] = doc_ids[idx]
            doc["text"] = doc_texts[idx]
            results.append(doc)
        return results
