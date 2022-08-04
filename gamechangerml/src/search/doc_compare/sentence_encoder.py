from txtai.embeddings import Embeddings
from txtai.ann import ANN
from os import remove
from os.path import join
from pickle import load
from pandas import DataFrame
from threading import current_thread
import numpy as np
import torch
import logging
import threading

from gamechangerml.api.utils.logger import logger
from gamechangerml.src.text_handling.corpus import LocalCorpus
from gamechangerml.src.text_handling.process import preprocess
from gamechangerml.src.model_testing.validation_data import MSMarcoData

logger = logging.getLogger(__name__)

class DocCompareSentenceEncoder:
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
        processmanager = None
    ):

        if model:
            self.encoder_model = model
        else:
            self.encoder_model = join(
                transformer_path, encoder_model_name)
        self.bert_tokenizer = None
        if bert_tokenize:
            self.bert_tokenizer = self.encoder_model
        self.min_token_len = min_token_len
        self.return_id = return_id
        self.verbose = verbose
        self.processmanager = processmanager
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
                embeddings[x] = load(queue)

        # Remove temporary file
        logger.info("Removing temporary file")
        remove(stream)
        logger.info("Making dataframe")
        all_text = []
        for para_id, text, _ in corpus:
            all_text.append([text, para_id])

        df = DataFrame(all_text, columns=["text", "paragraph_id"])

        embedding_path = join(index_path, "embeddings.npy")
        dataframe_path = join(index_path, "data.csv")
        ids_path = join(index_path, "doc_ids.txt")

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
            corpus = [(para_id, " ".join(tokens), None)
                      for tokens, para_id in corp]
            logger.info(
                f"\nLength of batch (in par ids) for indexing : {str(len(corpus))}"
            )

        else:
            logger.info(
                "Did not include path to corpus, making test index with msmarco data"
            )
            data = MSMarcoData()
            corpus = data.corpus
            if  self.processmanager:
                self.processmanager.update_status(
                    self.processmanager.training,
                    0,
                    1,
                    "building sent index",
                    thread_id=threading.current_thread().ident,
                )
        self._index(corpus, index_path)
        if  self.processmanager:
            self.processmanager.update_status(
                self.processmanager.training,
                1,
                1,
                "finished building sent index",
                thread_id=threading.current_thread().ident,
            )
        self.embedder.save(index_path)
        logger.info(f"Saved embedder to {index_path}")
