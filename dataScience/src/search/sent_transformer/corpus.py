import os
import re
import json
import random

import numpy as np

from collections import defaultdict
from tqdm import tqdm

from dataScience.src.text_handling.process import preprocess
from dataScience.src.featurization.doc_parser.parser import Hieharchy

class DirHieharchy(object):
    """
    Defines the hieharchy structure that
    makes nested dictionary update easier
    for directories
    """
    def __init__(self):
        self.dictionary = {}

    def update(self, keys, value):
        """
        Update the dictionary given a list
        of key and value to be assigned
        """
        dic = self.dictionary
        for key in keys[:-1]:
            if key not in dic:
                dic[key] = {}
            dic = dic[key]
        if keys[-1] not in dic:
            dic[keys[-1]] = []

        dic[keys[-1]].append(value)

class SentenceCorpus(object):
    """
    Defines a dataloader function that randomly retrieves
    sentences and items from the documents under the corpus
    directory

    Args:
        directory (str): Directory containing the documents with
        nested dictionary format
        verbose (bool): Print items
        iter_len (int): Max number of iterations to pull from this
        iterator

    """
    def __init__(self, directory, verbose = False, iter_len = 100):
        self.directory = directory
        self.file_list = [
            os.path.join(directory, file)
            for file in os.listdir(directory)
            if file[-5:] == ".json"
        ]
        self.verbose = verbose
        self.iter_len = iter_len
        self.iterator = None
        
        self._directory_parse(self.file_list)

    def _directory_parse(self, corpus_path):
        """
        Create a hieharchy for the DoD specific numbering
        system
        
        Args:
            corpus_path (str): Directory path for DoD corpus
        """
        dir_rank = DirHieharchy()
        for file in corpus_path:
            if not file.endswith("metadata.json"):
                metadata = self._find_meta(file)
                a = metadata["type"]
                b = metadata["series"]
                c = metadata["subseries"]
                d = metadata["number"]
                e = metadata["issuance"]
                dir_rank.update([a, b, c, d, e], metadata["path"])
            else:
                self.metadata = self._get_doc(file)
        self.dir_rank = dir_rank.dictionary

    def _find_meta(self, path):
        """
        Generate the meta information of each file path from its
        document name

        Args:
            path (str): File path 

        Return:
            doc_meta (dict): Dictionary containing meta information
                of file
        """

        # Extract series numbers from file
        doc_type = path.split()[0].split("/")[-1]
        doc_number = re.findall("\d{4}", path,  re.DOTALL)[0]
        doc_series = doc_number[0]
        doc_subseries = doc_number[:2]
        doc_issuance = re.findall("\.\d+", path, re.DOTALL)[0][1:]
        
        # Extract volume or chapter number if it exists
        path_l = path.lower()
        doc_vol = re.findall("volume\ \d{1,}", path_l, re.DOTALL)
        doc_vol = doc_vol[0].split()[-1] if doc_vol else None
        doc_chp = re.findall("ch\ \d{1,}", path_l, re.DOTALL)
        doc_chp = doc_chp[0].split()[-1] if doc_chp else None
        
        doc_meta = {
            "path": path,
            "type": doc_type,
            "series": doc_series,
            "subseries": doc_subseries,
            "issuance": doc_issuance,
            "number": doc_number,
            "volume": doc_vol,
            "chapter": doc_chp
        }
        return doc_meta

    def _pull_doc(self, doc = [], fname = None):
        """
        Pulls a document data if the path is given. If not,
        randomly pull a document from the corpus directory

        Args:
            doc (str/list): File path to document or list of 
                metadata information to filter through document
                hieharchy
        
        Return:
            doc (list): List of meta information for document
            doc_data (dict): Dictionary containing text from file
            fname (str): Filename of document
            fpath (str): File path to document
        """
        if isinstance(doc, str):
            doc_data = self._get_doc(doc)
            doc_meta = self._find_meta(doc)
            doc = [
                doc_meta["type"],
                doc_meta["series"],
                doc_meta["subseries"],
                doc_meta["number"],
                doc_meta["issuance"]
            ]
        else:
            dic = self.dir_rank
            if doc:
                for key in doc:
                    dic = dic[key]
            else:
                doc = []
            while isinstance(dic, dict):
                key = random.sample(list(dic.keys()), 1)[0]
                dic = dic[key]
                doc.append(key)
            
            if fname:
                fpath = [path for path in dic if fname in path]
                if len(fpath) > 0:
                    fpath = fpath[0]
                else:
                    fpath = random.sample(dic, 1)[0]
            else:
                fpath = random.sample(dic, 1)[0]
            fname = fpath.split("/")[-1].replace("_parsed", "")
            fname = self.metadata[fname]
            doc_data = self._get_doc(fpath)
        return doc, doc_data, fname, fpath

    def _pull_text(self, doc_data, headers = []):
        """
        Function to pull a text from the hierarchy based
        document parsed
        
        Args:
            doc_data (dict): Dictionary of hierachy based data
            headers (list): List of headers to filter out potential
                text

        Return:
            headers (list): Complete list of headers referencing
                the text
            text (str): Text under the set of headers
        """
        dic = doc_data

        # Filter dictionary to specific headers
        header_text = []
        if headers:
            for key in headers:
                dic = dic[key]
                if isinstance(dic, str):
                    header_text.append(dic)
                else:
                    header_text.append(dic["text"])
        else:
            headers = []

        # Randomly explore the hierarchy and append section text
        # and generate the header and text data
        while (len(dic) > 1) and (isinstance(dic, dict)):
            key = random.sample(dic.keys(), 1)[0]
            dic = dic[key]
            if "text" in dic:
                if isinstance(dic, str):
                    header_text.append(dic)
                else:
                    header_text.append(dic["text"])
            if key != "text":
                headers.append(key)
        header_text = ". ".join(header_text)
        if "text" in dic:
            if isinstance(dic, str):
                text = dic
            else:
                text = dic["text"]
        else:
            text = ""

        return headers, text

    def _get_sample(self, doc_meta = None, headers = None, fpath = None):
        """
        Pull a sample text from the corpus. If provided some meta information,
        the information will be used to pull from a smaller subset of data to
        achieve a specific similarity score

        Args:
            doc_meta (list): List of meta data found in the directory hieharchy
            headers (list)
        """
        doc_info, doc_data, fname, fpath = self._pull_doc(doc_meta, fpath)
        doc_headers, text = self._pull_text(doc_data, headers)
        return text, doc_info, doc_headers, fname, fpath

    def _get_item_sample(self):
        """
        Randomly pull a sentence pair from the corpus and return
        a similarity level of the pair

        Return:
            sample_1 (list): List containing text and meta information
            about returned text

            sample_2 (list): Similar with sample_1 but different text

            sim_level: Level of similarity between text meta information.
            Scale from 1 (least similar) to 9 (most similar)
        """
        text = ""
        while len(text) <= 10:
            # Get a random sample from the corpus
            sample_1 = self._get_sample()

            # Extract meta information from the sample
            doc_meta_len = len(sample_1[1])
            meta_copy = sample_1[1] + sample_1[2]

            # Generate a random probability of selecting
            # a section of the meta information
            meta_len = list(range(1, len(meta_copy) + 1))
            meta_prob = [i/sum(meta_len) for i in meta_len]
            sim_level = np.random.choice(meta_len, p = meta_prob) - 1 
            meta_copy = meta_copy[:sim_level]
            doc_meta = meta_copy[:doc_meta_len]
            headers = meta_copy[doc_meta_len:]

            # Pull a second sample from the headers
            # for potential similarity
            sample_2 = self._get_sample(doc_meta, headers, sample_1[4])

            # Get second text
            text = sample_1[0] if len(sample_1[0]) < len(sample_2[0]) else sample_2[0]
        return sample_1, sample_2, sim_level

    def __iter__(self):
        """
        Yield a sentence pair with similarity level
        """
        for _ in range(self.iter_len):
            sample_1, sample_2, sim_level = self._get_item_sample()
            yield sample_1, sample_2, sim_level

    def _get_doc(self, fpath):
        """
        Load a JSON File
        Args:
            fpath (str): File path of JSON file
        """
        with open(fpath, "r") as fp:
            data = json.load(fp)
        return data
