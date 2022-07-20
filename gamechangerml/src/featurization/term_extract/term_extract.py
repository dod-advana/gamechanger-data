import fnmatch
import json
import logging
import os
import re
from collections import Counter
from operator import itemgetter

import en_core_web_sm
from spacy.matcher import Matcher

from gamechangerml.configs.config import DefaultConfig as Config
import gamechangerml.src.modelzoo.semantic.term_extract.version_ as v

logger = logging.getLogger("gamechanger")


class TermExtractor(object):
    noun, adj, prep = (
        {"POS": "NOUN", "IS_PUNCT": False},
        {"POS": "ADJ", "IS_PUNCT": False},
        {"POS": "DET", "IS_PUNCT": False},
    )

    patterns = [
        [adj],
        [{"POS": {"IN": ["ADJ", "NOUN"]}, "OP": "*", "IS_PUNCT": False}, noun],
        [
            {"POS": {"IN": ["ADJ", "NOUN"]}, "OP": "*", "IS_PUNCT": False},
            noun,
            prep,
            {"POS": {"IN": ["ADJ", "NOUN"]}, "OP": "*", "IS_PUNCT": False},
            noun,
        ],
    ]

    entities = ["ORG"]

    __version__ = v.__version__

    def __init__(self, max_term_length=2, min_freq=2, ner=False):
        """
        Term extraction using parts-of-speech.

        Args:
            max_term_length (int): extracts `patterns` up the length of
                this argument

            min_freq (int): minimum term frequency for constructing the
                final output

            ner (bool): if True, adds organization named entity to the
                term counts. NB this adds significant time to the
                processing
        """
        if max_term_length < 2:
            raise ValueError("max_tokens must be > 1")
        if max_term_length > 5:
            raise ValueError("max_tokens must be < 5")
        if min_freq <= 0:
            raise ValueError("min_freq must be > 0")

        self.ner = ner
        self.min_freq = min_freq

        self.max_tokens = max_term_length
        if self.ner:
            self.nlp = en_core_web_sm.load(disable=["parser"])
        else:
            self.nlp = en_core_web_sm.load(disable=["ner", "parser"])
        self.matcher = Matcher(self.nlp.vocab)

        logger.info(
            "{} version {}".format(self.__class__.__name__, self.__version__)
        )

    @staticmethod
    def _word_length(string):
        return string.count(" ") + 1

    @staticmethod
    def _clean(string):
        cleaned = re.sub("\\n", " ", string)
        cleaned = re.sub("[\u201c\u201d]+", "", cleaned, re.U)
        cleaned = re.sub('"', "", cleaned)
        cleaned = re.sub("(?:\\d+\\.)+", " ", cleaned)
        cleaned = re.sub("- {2,}", " ", cleaned)
        cleaned = re.sub("\\.\\.{2,}", " ", cleaned)
        cleaned = re.sub("\\(\\w\\)", " ", cleaned, re.I)
        cleaned = re.sub("\\w\\. ?", " ", cleaned, re.I)
        return re.sub("\\s{2,}", " ", cleaned)

    def count_from_document(self, document):
        """
        Counts patterns and optionally, named entities from a single document.

        Args:
            document (str): input document

        Returns:
            Counter

        """
        term_counter = Counter()

        def add_to_counter(matcher, doc, idx, matches):
            match_id, start, end = matches[idx]
            candidate = str(doc[start:end])
            if 1 < self._word_length(candidate) <= self.max_tokens:
                term_counter[candidate] += 1

        for i, pattern in enumerate(TermExtractor.patterns):
            self.matcher.add("term_{}".format(i), add_to_counter, pattern)

        doc = self.nlp(document)
        _ = self.matcher(doc)

        if self.ner:
            ent_counter = self._count_entities(doc)
            term_counter.update(ent_counter)

        return term_counter

    @staticmethod
    def _count_entities(doc):
        ents = [
            re.sub("^the ", "", ent.text)
            for ent in doc.ents
            if ent.label_ in TermExtractor.entities
        ]
        ent_counter = Counter({ent: 1 for ent in ents})
        return ent_counter

    @staticmethod
    def gen_json(data_dir=Config.DATA_DIR):
        """
        Generator to read and extract the `text` from a JSON file in the
        `data_dir`.

        Args:
            data_dir (str): path to the JSON files

        Yields:
            str

        Raises:
            ValueError if the directory is not valid
            JSONDecodeError if json.load() fails
            IOError, RuntimeError if there is a problem
                opening or reading a file

        """
        if not os.path.isdir(data_dir):
            raise ValueError("invalid data_dir, got {}".format(data_dir))

        try:
            for file_ in os.listdir(data_dir):
                if fnmatch.fnmatch(file_, "*.json"):
                    with open(os.path.join(data_dir, file_)) as fp:
                        j_doc = json.load(fp)
                    if "text" in j_doc:
                        yield j_doc["text"]
                    else:
                        logger.warning("no 'text' key in {}".format(file_))
        except (IOError, json.JSONDecodeError, RuntimeError) as e:
            logger.exception("{}: {}".format(type(e), str(e)), exc_info=True)
            raise

    def generate_counts(self, data_dir=Config.DATA_DIR):
        """
        Generator to read and process successive JSON files.

        Args:
            data_dir (str): path to the JSON files

        Yields:
            Counter
        """
        technical_counts = Counter()
        for text in self.gen_json(data_dir):
            doc_count = self.count_from_document(self._clean(text.lower()))
            technical_counts.update(doc_count)
            yield technical_counts

    @staticmethod
    def _make_output(final_count, min_freq):
        by_key = dict(sorted(final_count.items(), key=itemgetter(0)))
        suggests = [
            {"input": term, "weight": weight}
            for term, weight in by_key.items()
            if weight >= min_freq
        ]
        return suggests

    def count_from_dir(self, max_files=None, data_dir=Config.DATA_DIR):
        """
        Counts patterns from JSON files in `data_dir`. For each 1-gram
        prefix, a list of suffix, frequency tuples is created.

        Args:
            max_files (int|None): optional; maximum number of files to
                consider for processing.

            data_dir (str): path to the JSON files

        Returns:
            dict
        """
        final_counter = dict()
        f_count = 0

        for tech_counts in self.generate_counts(data_dir):
            final_counter = tech_counts
            f_count += 1
            if max_files is not None and f_count == max_files:
                break
            if f_count in [1, 5, 10] or f_count % 25 == 0:
                logger.debug("processed {:>5,}".format(f_count))

        logger.debug("total files processed : {:,}".format(f_count))
        prefix_order = self._make_output(final_counter, self.min_freq)
        logger.debug("total terms: {:,}".format(len(prefix_order)))
        return prefix_order
