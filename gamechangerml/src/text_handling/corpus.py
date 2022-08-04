import os
import json
import threading

# import pandas as pd
from gensim.models.doc2vec import TaggedDocument
from gamechangerml.src.text_handling.process import preprocess, get_tokenizer
from gamechangerml.src.utilities.text_utils import check_quality_paragraph
from gamechangerml.api.utils import processmanager
from tqdm import tqdm


class LocalCorpus(object):
    def __init__(
        self,
        directory,
        return_id=False,
        min_token_len=3,
        verbose=False,
        bert_based_tokenizer=None,
        files_to_use=None,
    ):
        self.directory = directory
        if files_to_use:  ## if we only want to do this on a subset
            self.file_list = list(
                set([os.path.join(directory, i) for i in files_to_use]).intersection(
                    [
                        os.path.join(directory, file)
                        for file in os.listdir(directory)
                        if file[-5:] == ".json"
                    ]
                )
            )
        else:
            self.file_list = [
                os.path.join(directory, file)
                for file in os.listdir(directory)
                if file[-5:] == ".json"
            ]
        self.file_list
        self.return_id = return_id
        self.min_token_len = min_token_len
        self.verbose = verbose
        self.bert_based_tokenizer = bert_based_tokenizer
        if self.bert_based_tokenizer:
            self.auto_token = get_tokenizer(self.bert_based_tokenizer)

    def __iter__(self):
        if self.verbose:
            iterator = tqdm(self.file_list)
        else:
            iterator = self.file_list

        total = len(self.file_list)
        progress = 0
        processmanager.update_status(
            processmanager.loading_corpus,
            progress,
            total,
            thread_id=threading.current_thread().ident,
        )
        for file_name in iterator:
            try:
                doc = self._get_doc(file_name)
                paragraphs = [p["par_raw_text_t"] for p in doc["paragraphs"]]
                paragraph_ids = [p["id"] for p in doc["paragraphs"]]
                for para_text, para_id in zip(paragraphs, paragraph_ids):
                    if self.bert_based_tokenizer:
                        tokens = self.auto_token.tokenize(para_text)
                    else:
                        tokens = preprocess(para_text, min_len=1)
                    if tokens:
                        if check_quality_paragraph(tokens, para_text):
                            if len(tokens) > self.min_token_len:
                                if self.return_id:
                                    yield tokens, para_id
                                else:
                                    yield tokens

                progress += 1
                processmanager.update_status(
                    processmanager.loading_corpus,
                    progress,
                    total,
                    thread_id=threading.current_thread().ident,
                )
            except Exception as e:
                print(e)
                print(f"Error with {file_name} in creating local corpus")
                
    def _get_doc(self, file_name):
        with open(file_name, "r") as f:
            line = f.readline()
            line = json.loads(line)
        return line


class LocalTaggedCorpus(object):
    def __init__(self, directory, phrase_detector):
        self.directory = directory
        self.file_list = [
            os.path.join(directory, file)
            for file in os.listdir(directory)
            if file[-5:] == ".json"
        ]

        self.phrase_detector = phrase_detector

    def __iter__(self):
        for file_name in self.file_list:
            # get the docs and ingest the json
            doc = self._get_doc(file_name)

            for p in doc["paragraphs"]:
                # paragraph tokens for training
                tokens = preprocess(
                    p["par_raw_text_t"],
                    phrase_detector=self.phrase_detector,
                    remove_stopwords=True,
                )
                # creating paragraph tag for model
                filename = p["filename"]
                para_num = str(p["par_inc_count"])
                para_id = "_".join((filename, para_num))
                # if paragraph is long enough yield for training
                if len(tokens) > 10:  # to account for the windowsize with d2v
                    yield TaggedDocument(tokens, [para_id])

    def _get_doc(self, file_name):
        with open(file_name, "r") as f:
            line = f.readline()
            line = json.loads(line)
        return line
