import os
import json
#import pandas as pd
from gensim.models.doc2vec import TaggedDocument
from dataScience.src.text_handling.process import preprocess
from tqdm import tqdm

class LocalCorpus(object):
    def __init__(self, directory, return_id = False, min_token_len = 3, verbose = False):
        self.directory = directory
        self.file_list = [
            os.path.join(directory, file)
            for file in os.listdir(directory)
            if file[-5:] == ".json"
        ]
        self.file_list
        self.return_id = return_id
        self.min_token_len = min_token_len
        self.verbose = verbose

    def __iter__(self):
        if self.verbose:
            iterator = tqdm(self.file_list)
        else:
            iterator = self.file_list

        for file_name in iterator:
            doc = self._get_doc(file_name)
            paragraphs = [
                p['par_raw_text_t']
                for p in doc['paragraphs']
                ]
            paragraph_ids = [
                p['id']
                for p in doc['paragraphs']
            ]
            for para_text, para_id in zip(paragraphs, paragraph_ids):
                tokens = preprocess(para_text, min_len=1)
                if len(tokens) > self.min_token_len:
                    if self.return_id:
                        yield tokens, para_id
                    else:
                        yield tokens

    def _get_doc(self, file_name):
        with open(file_name, "r") as f:
            line = f.readline()
            line = json.loads(line)
        return line

class SentCorpus(object):
    def __init__(self, directory, return_id = False, min_token_len = 3, verbose = False):
        self.directory = directory
        self.file_list = [
            os.path.join(directory, file)
            for file in os.listdir(directory)
            if (file[-5:] == ".json")
            and ("metadata" not in file)
        ]
        self.return_id = return_id
        self.min_token_len = min_token_len
        self.verbose = verbose
        self.metadata = self._get_doc(os.path.join(directory, "metadata.json"))

    def __iter__(self):
        if self.verbose:
            iterator = tqdm(self.file_list)
        else:
            iterator = self.file_list

        for file_name in iterator:
            doc = self._get_doc(file_name)
            doc_data = self._get_sentences(doc)
            fname = file_name.split("/")[-1].replace(".json", "")
            file_full_name = self.metadata[fname.replace("_parsed", "") + ".json"]

            for idx, pair in enumerate(doc_data):
                sentence, old_id = pair
                sent_idx = fname + "_" + str(idx)
                tokens = [file_full_name] + sentence.split()
                if self.return_id:
                    yield tokens, sent_idx, old_id
                else:
                    yield tokens

    def _get_sentences(self, nested_dict, headers = [], min_token_len = 10):
        sentences = []
        text = None
        old_id = None
        for key, value in nested_dict.items():
            if isinstance(value, dict):
                sub_sentences = self._get_sentences(value, headers + [key])
                sentences.extend(sub_sentences)
            else:
                if (key == "text") and (len(value) >= min_token_len):
                    text = value
                else:
                    old_id = value
        if (text is not None) and (old_id is not None):
            sentences.append((" ".join(headers) + " [SEP] " + text, old_id))
        return sentences

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

            for p in doc['paragraphs']:
                # paragraph tokens for training
                tokens = preprocess(
                    p['par_raw_text_t'],
                    phrase_detector=self.phrase_detector,
                    remove_stopwords=True)
                # creating paragraph tag for model
                filename = p['filename']
                para_num = str(p['par_inc_count'])
                para_id = '_'.join(
                    (filename, para_num)
                )
                # if paragraph is long enough yield for training
                if len(tokens) > 10: #to account for the windowsize with d2v
                    yield TaggedDocument(tokens, [para_id])

    def _get_doc(self, file_name):
        with open(file_name, "r") as f:
            line = f.readline()
            line = json.loads(line)
        return line       