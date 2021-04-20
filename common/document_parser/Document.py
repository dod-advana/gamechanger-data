"""
Class definition for Document, Issuance, Page
"""

import fitz
import json
import re
import string
import pandas as pd
from pathlib import Path
from common.document_parser import issuance_ref
from common.document_parser import dates_extract
from common.utils.file_utils import is_pdf, is_ocr_pdf, is_encrypted_pdf
from collections import defaultdict
import typing as t
import filetype
import shutil

import multiprocessing
import logging
from . import get_default_logger
import datetime

import syntok.segmenter as segmenter
import os
from dataPipelines.gc_ocr.utils import PDFOCR, OCRJobType, OCRError
# from dataScience.src.featurization.summary import GensimSumm
from dataScience.src.featurization.keywords.extract_keywords import get_keywords
from dataScience.models.topic_models.tfidf import bigrams, tfidf_model
from dataScience.src.text_handling.process import topic_processing
from dataScience.src.featurization.abbreviation import expand_abbreviations
from dataScience.src.search.ranking.features import (
    get_pr,
    get_orgs,
    get_kw_score,
    get_txt_length,
)

import dataScience.src.utilities.spacy_model as spacy_
from dataScience.src.utilities.text_utils import simple_clean
from dataScience.configs.config import BertSummConfig

from operator import itemgetter

cwd = os.getcwd()

spacy_model = spacy_.get_lg_nlp()


class UnparseableDocument(Exception):
    """Document was unsuitable for parsing, for some reason"""
    pass


class Document:
    """
    A class to represent a document
    """

    def __init__(self, f_name: Path):
        """
        constructs necessary attributes for the document object
        Args:
            f_name: the filename
        """

        self.type = "document"
        self.f_name = (
            f_name.absolute().name
            if isinstance(f_name, Path)
            else Path(str(f_name)).name
        )

    def process_dir(self, dir_path: str):
        pass


class Issuance(Document):
    """
    A class to represent Issuance
    """

    def __init__(self, f_name, f_type="pdf", meta_data=None, ocr_missing_doc=False, num_ocr_threads=2, ultra_simple=False):
        """
        constructs necessary attributes for the Issuance class

        Args:
            f_name: the filename
            f_type: the file type
            meta_data: Meta data from ingestion to be passed here as a json file
        """
        self.meta_data = meta_data

        if self.meta_data:
            self.deconstruct_meta()
            self.access_timestamp = self.meta_data["access_timestamp"]
        if f_type == "json":
            self.json_read(f_name)
        elif f_type == "pdf":
            if ocr_missing_doc:
                if not is_ocr_pdf(str(f_name)) and not is_encrypted_pdf(str(f_name)):
                    ocr = PDFOCR(
                        input_file=f_name,
                        output_file=f_name,
                        ocr_job_type=OCRJobType.SKIP_TEXT, # best to force OCR if the earlier OCR checks failed anyway
                        ignore_init_errors=True,
                        num_threads=num_ocr_threads
                    )
                    ocr.convert_in_subprocess(raise_error=True)
                    f_name = str(ocr.output_file)
            self.pdf_read(f_name, ultra_simple)
        else:
            print("File Type was not specified correctly")

        self.construct()

    def construct(self):
        """
        Get information from the file
        """
        self.get_dates()
        self.get_entities()
        self.get_author()
        self.get_signature()
        self.get_subject()
        self.get_title()
        self.get_word_count()
        self.get_classification()
        self.get_group()

    def deconstruct_meta(self):
        """
        Deconstructs and loads the metadata

        """
        if type(self.meta_data) == dict:
            pass
        else:
            if type(self.meta_data) == str:
                meta_fname = Path(self.meta_data)
            else:
                meta_fname = self.meta_data

            with open(meta_fname) as f_in:
                self.meta_data = json.load(f_in)

    # TODO: add opt arg to raise errors
    # TODO: add callback or conditions that throw errors if doc is
    #  too short and has FOUO (or something like that), in order to
    #  avoid processing docs that are just placeholder messages for the real doc
    def pdf_read(self, f_name: Path, ultra_simple=False):
        """
        Reads the pdf file and gets important information
        Args:
            f_name: location of the pdf file

        """

        Document.__init__(self, f_name)

        self.iss_type = self.get_iss_type()
        self.doc_num = self.get_doc_number()
        self.extract_text(f_name, ultra_simple=ultra_simple)

        if ultra_simple:
            rank_min = 0.00001
            self.ref_list = list()
            self.abbreviations = []
            self.summary = ''
            self.pagerank = rank_min
            self.orgs = {}
            self.txt_length = rank_min
            self.kw_doc_score = rank_min
            self.keyw = []
        else:
            self.ref_list = self.get_ref_list()
            text, self.abbreviations = expand_abbreviations(self.text)
            self.summary = self.get_summary()
            self.pagerank = get_pr(self.id)
            self.orgs = get_orgs(self.id)
            self.txt_length = get_txt_length(self.id)
            self.kw_doc_score = get_kw_score(self.id)
            keyword_counts = defaultdict(int)
            for l in self.keywords:
                for kw in l:
                    keyword_counts[kw] += 1
            kw_list = list(zip(keyword_counts.values(), keyword_counts.keys()))
            kw_list.sort(reverse=True)
            self.keyw = [x[1] for x in kw_list[:10]]

    def get_summary(self):

        if len(self.text) < BertSummConfig.MODEL_ARGS['doc_limit']:
            long_doc = False
        else:
            long_doc = True

        # try:
        #     return GensimSumm(self.text, long_doc=long_doc, word_count=30).make_summary()
        # except:
        #     return ""

        return ""

    def get_dates(self):
        """
        get dates from the text and metadata

        """

        self.ingest_date = False

        if self.meta_data:
            if "access_timestamp" in self.meta_data:
                self.ingest_date = self.meta_data["access_timestamp"]

        self.date_list = dates_extract.dates_to_list(self.text)
        self.init_date = "NA"
        self.change_date = "NA"

        return None

    def get_entities(self):
        """
        Get Entities

        """
        self.entities = ["NA_1", "NA_2"]
        return None

    def get_author(self):
        """
        Get the Author

        """
        self.author = "NA"
        return None

    def get_signature(self):
        """
        get the signature

        """

        self.signature = "NA"
        return None

    def get_subject(self):
        """
        get the subject

        """

        self.subject = "NA"
        return None

    def get_title(self):
        """
        Get the title

        """

        if self.meta_data:
            self.title = self.meta_data["doc_title"]
        else:
            self.title = "NA"

    def get_word_count(self):
        """
        get the word count

        """

        self.word_count = len(self.text.split(" "))
        return None

    def get_iss_type(self):
        """
        get document type
        Returns: the document type as a string

        """

        if self.meta_data:
            if "doc_type" in self.meta_data:
                m_type = self.meta_data["doc_type"]
                return m_type

        m_type = str(self.f_name).split(" ")[0]

        return m_type

    def get_doc_number(self):
        """
        get the document number

        Returns: the document number as a string

        """

        if self.meta_data:
            if "doc_num" in self.meta_data:
                m_num = self.meta_data["doc_num"]
                return m_num

        m_num = str(self.f_name).split(",")[0].split(" ")[-1]
        return m_num

    def get_ref_list(self):
        """
        gets the reference list
        Returns: reference list

        """

        iss_ref = issuance_ref.collect_ref_list(self.text)
        return list(iss_ref)

    def get_classification(self):
        """
        gets classification

        """

        self.classification = "NA"
        return None

    def get_group(self):
        """
        get the group

        """

        self.group = self.id

    def __str__(self):
        """
        count the number of pages
        Returns: the number of pages as a string

        """

        print_text = str(self.f_name) + " has " + str(self.page_count) + " pages"
        return print_text

    def json_write(self, clean=False, out_dir="./", skip_optional_ds=False, ultra_simple=False) -> bool:
        """
        Writes a Json file containing gathered information about the pdf
        Args:
            clean: boolean to determine if text is to be cleaned or not. The text is cleaned from special characters and extra spaces
            out_dir: output directory for resulting json

        Returns: True if the operation was successful

        """
        self.topics_rs = {}
        if not skip_optional_ds and not ultra_simple:
            self.extract_entities()
            self.extract_topics()

        ex_pages = []

        for items in self.pages:
            if clean:
                m_text = self.clean_text(items.p_text)
            else:
                m_text = items.p_text
            p_dict = {
                "type": items.type,
                "id": items.p_id,
                "filename": items.f_name,
                "p_page": items.p_num,
                "p_text": m_text.encode('utf-8', 'ignore').decode('utf-8'),
                "p_raw_text": items.p_text,
            }
            ex_pages.append(p_dict)

        ex_par = []
        if not ultra_simple:
            for items in self.paragraphs_obj:
                par_dict = {
                    "type": items.type,
                    "id": items.pa_id,
                    "filename": items.f_name,
                    "page_num_i": items.page_num,
                    "par_raw_text_t": items.pa_raw_text.encode('utf-8', 'ignore').decode('utf-8'),
                    "par_count_i": items.pa_num,
                    "par_inc_count": items.par_inc_count,
                    "entities": items.pa_entities
                }

                ex_par.append(par_dict)

        if clean:
            b_text = self.clean_text(self.text)
        else:
            b_text = self.text
        ex_dict = {
            "type": self.type,
            "id": self.id,
            "filename": self.f_name,
            "page_count": self.page_count,
            "par_count_i": self.total_page_count,
            "doc_type": self.iss_type,
            "doc_num": self.doc_num,
            "ref_list": self.ref_list,
            "summary_30": self.summary,
            "abbreviations_n": self.abbreviations,
            "init_date": self.init_date,
            "change_date": self.change_date,
            "entities": self.entities,
            "author": self.author,
            "signature": self.signature,
            "subject": self.subject,
            "title": self.title,
            "word_count": self.word_count,
            "classification": self.classification,
            "group_s": self.group,
            "keyw_5": self.keyw,
            "paragraphs": ex_par,
            "text": b_text,
            "raw_text": self.text.encode('utf-8', 'ignore').decode('utf-8'),
            "pages": ex_pages,
            "pagerank_r": self.pagerank,
            "kw_doc_score_r": self.kw_doc_score,
            "orgs_rs": self.orgs,
            "topics_rs": self.topics_rs,
            "text_length_r": self.txt_length
        }

        # Add metadata extensions to the root json
        if self.meta_data:
            if "extensions" in self.meta_data:
                extensions = self.meta_data["extensions"]
                for key in extensions:
                    ex_dict[key] = extensions[key]

        outname = Path(self.f_name).stem + '.json'

        p = Path(out_dir)
        if not p.exists():
            p.mkdir()

        with open(p.joinpath(outname), "w") as fp:
            json.dump(ex_dict, fp)

        return True

    def extract_text(self, f_name: Path, ultra_simple=False) -> bool:
        """
        extract text from the pdf file
        Args:
            f_name: location of the file

        Returns: True if the operation was successful

        """

        doc = fitz.open(f_name)

        self.page_count = doc.pageCount
        if self.page_count < 1:
            doc.close()
            raise UnparseableDocument(f"Could not parse the doc, failed page count check: {f_name}")

        self.id = str(self.f_name) + "_0"

        page = 0
        par_inc_count = 0
        self.total_page_count = 0
        self.text = ""
        self.pages = []
        self.keywords = []
        self.paragraphs_obj = []

        while page < self.page_count:
            p = doc.loadPage(page)
            p_text = p.getText()
            p_keyw = get_keywords(p_text)
            self.keywords.append(p_keyw)
            self.text = self.text + p_text
            m_page = Page(self.f_name, page, p_text, p_keyw=p_keyw)
            self.pages.append(m_page)
            if ultra_simple:
                par_count = -1
            else:
                par_count = 0
                for paragraph in segmenter.process(p_text):
                    par_text = ""

                    for sentence in paragraph:
                        sentence_text = " ".join(
                            [token.value for token in sentence]
                        )
                        par_text += sentence_text

                    par = Paragraph(
                        self.f_name,
                        par_count,
                        self.clean_text(par_text),
                        page,
                        par_inc_count,
                        par_text
                    )
                    self.paragraphs_obj.append(par)
                    par_count += 1
                    par_inc_count += 1
                    self.total_page_count += 1
            page += 1

        self.par_count = par_count

        # TODO: decide if this should be a cmdline option
        # text_file = open("sample.txt", "w")
        # n = text_file.write(self.text.encode("utf-8", "replace").decode('utf-8'))
        # text_file.close()
        doc.close()

        if self.text == "":
            return False

        return True

    def clean_text(self, doc_text: str) -> str:
        """
        The text is cleaned from special characters and extra spaces
        Args:
            doc_text: input text to be cleaned

        Returns:

        """

        text = doc_text.replace("\n", " ")
        text = re.sub(r"\s+", " ", text)
        remove = string.punctuation + "”“"
        remove = remove.replace(".", "")

        text = text.translate({ord(i): None for i in remove})

        return text

    def json_read(self, f_name: str) -> None:
        """
        Reads a Json file and gathers relevant information
        Args:
            f_name: location of the relevant file

        """

        with open(f_name) as f_in:
            doc_dict = json.load(f_in)

        Document.__init__(self, doc_dict["filename"])

        self.id = doc_dict["id"]
        self.page_count = doc_dict["page_count"]
        self.text = doc_dict["text"]
        self.raw_text = doc_dict["raw_text"]
        self.iss_type = doc_dict["doc_type"]
        self.doc_num = doc_dict["doc_num"]
        self.ref_list = doc_dict["ref_list"]
        text, self.abbreviations = expand_abbreviations(self.text)
        self.summary = self.get_summary()
        self.pagerank = get_pr(self.id)
        self.orgs = get_orgs(self.id)
        # self.topics = doc_dict["topics_rs"] #TODO: read in topics
        self.kw_doc_score = get_kw_score(self.id)
        self.txt_length = get_txt_length(self.id)

        self.construct()

        self.keywords = []
        self.total_par_count = 0
        self.pages = []
        for item in doc_dict["pages"]:
            p_page = item.get("p_page", "0")
            p_text = item.get("p_text", "")
            p_raw_text = item.get("p_raw_text", "")
            p_keyw = get_keywords(p_raw_text)
            self.keywords.append(p_keyw)
            m_page = Page(self.f_name, p_page, p_text, p_keyw, p_raw_text)
            self.pages.append(m_page)

        keyword_counts = defaultdict(int)
        for l in self.keywords:
            for kw in l:
                keyword_counts[kw] += 1
        kw_list = list(zip(keyword_counts.values(), keyword_counts.keys()))
        kw_list.sort(reverse=True)
        self.keyw = [x[1] for x in kw_list[:10]]

        self.paragraphs_obj = []
        par_count = 0

        for item in doc_dict["paragraphs"]:
            pa_text = item["par_text_t"]
            pa_num = item["par_count_i"]
            pa_inc_count = item["par_inc_count"]
            page_num = item["page_num_i"]
            pa_raw_text = item["par_raw_text_t"]
            pa_entities = item["entities"]
            par = Paragraph(
                self.f_name,
                pa_num,
                pa_text,
                page_num,
                pa_inc_count,
                pa_raw_text,
                pa_entities
            )

            self.paragraphs_obj.append(par)
            par_count += 1
        self.par_count = par_count
        self.total_par_count += self.par_count


    def extract_topics(self):
        topics = tfidf_model.get_topics(topic_processing(self.text, bigrams), topn=5)
        for score, topic in topics:
            topic = topic.replace('_',' ')
            self.topics_rs[topic] = score

    def extract_entities(self):
        # get entities in each page. then, check if the entities are mentioned in the paragraphs and append
        # to paragraph  metadata.
        page_dict = {}
        for page in self.pages:
            page_text = page.p_text.encode('utf-8', 'ignore').decode('utf-8')
            page_text = simple_clean(page_text)
            doc = spacy_model(page_text)
            page_dict[page.p_num] = doc

        for par in self.paragraphs_obj:
            entities = {
                "ORG": [],
                "GPE": [],
                "NORP": [],
                "LAW": [],
                "LOC": [],
                "PERSON": [],
            }
            par_text = par.pa_raw_text.encode('utf-8', 'ignore').decode('utf-8')
            par_text = simple_clean(par_text)
            doc = page_dict[par.page_num]
            for entity in doc.ents:
                if (
                        entity.label_
                        in ["ORG", "GPE", "LOC", "NORP", "LAW", "PERSON"]
                        and entity.text in par_text
                ):
                    entities[entity.label_].append(entity.text)

            entity_json = {"ORG_s": list(set(entities["ORG"])), "GPE_s": list(set(entities["GPE"])),
                           "NORP_s": list(set(entities["NORP"])), "LAW_s": list(set(entities["LAW"])),
                           "LOC_s": list(set(entities["LOC"])), "PERSON_s": list(set(entities["PERSON"]))}
            par.pa_entities = entity_json

    def to_dict(self, full_text: bool = True, clean: bool = False) -> dict:
        """
        Stores relevant information into a dict
        Args:
            full_text: if True, the full text is saved to the dict
            clean: if True, The text is cleaned from special characters and extra spaces

        Returns:

        """
        if clean:
            b_text = self.clean_text(self.text)
        else:
            b_text = self.text

        ex_dict = {
            "type": self.type,
            "id": self.id,
            "filename": self.f_name,
            "page_count": self.page_count,
            "par_count_i": self.total_par_count,
            "doc_type": self.iss_type,
            "doc_num": self.doc_num,
            "ref_list": self.ref_list,
            "summary_30": self.summary,
            "keyw_5": self.keyw,
            "abbreviations_n": self.abbreviations,
            "init_date": self.init_date,
            "change_date": self.change_date,
            "entities": self.entities,
            "author": self.author,
            "signature": self.signature,
            "subject": self.subject,
            "title": self.title,
            "word_count": self.word_count,
            "classification": self.classification,
            "group_s": self.group,
            "pagerank_r": self.pagerank,
            "kw_doc_score_r": self.kw_doc_score,
            "orgs_rs": self.orgs,
            "text_length_r": self.txt_length
        }

        if full_text:
            ex_dict["text"] = b_text

        return ex_dict

    @staticmethod
    def create_csv_data(dir_path: str, out_dir: str = "./") -> None:
        """
        create csv data from Json
        Args:
            dir_path: directory where Json is stored
            out_dir: output directory for resulting csv

        """

        p = Path(dir_path).glob("**/*.json")
        files = [x for x in p if x.is_file()]

        doc_logger = get_default_logger()
        doc_logger.info("Creating CSV for #%i of Documents", len(files))

        iss_list = []
        for m_file in files:
            iss = Issuance(m_file, f_type="json")
            iss_list.append(iss.to_dict(full_text=False, clean=False))

        df = pd.DataFrame(iss_list)
        df.reset_index(drop=True, inplace=True)
        df.to_csv(out_dir + dir_path.split("/")[-1] + ".csv")

    @staticmethod
    def rewrite_dir(dir_path: str, out_dir: str) -> None:
        """
        takes in and recreates Json files
        Args:
            dir_path: directory where Json is stored
            out_dir: output directory for resulting Json

        """
        p = Path(dir_path).glob("**/*.json")
        files = [x for x in p if x.is_file()]

        doc_logger = get_default_logger()
        doc_logger.info("Rewriting Documents: %i", len(files))

        for m_file in files:
            iss = Issuance(m_file, f_type="json")
            iss.json_write(clean=False, out_dir=out_dir)


class Page:
    """
    A class to represent a page
    """

    page_type = "page"

    def __init__(self, f_name: str, p_num: int, p_text: str, p_keyw: t.List[str], p_raw_text: str = None):
        """
        constructs necessary attributes for the Page object

        Args:
            f_name: the location of the file
            p_num: the page number of the page
            p_text: the text on the page
            p_keyw: a list of keywords
            p_raw_text: the raw text on the page
        """

        self.f_name = f_name
        self.p_num = p_num
        self.p_text = p_text
        self.p_raw_text = p_raw_text
        self.p_keyw = p_keyw
        self.p_id = str(f_name) + "_" + str(p_num)
        self.type = "page"


class Paragraph:
    """
        constructs necessary attributes for the paragraph object
    """

    def __init__(
            self,
            f_name: str,
            pa_num: int,
            pa_text: str,
            page: str,
            par_inc_count: str,
            pa_raw_text: str = None,
            pa_entities: t.List[t.Dict[str, t.List[str]]] = [],
    ):
        """
        constructs necessary attributes for the paragraph object
        Args:
            f_name: the location of the file
            pa_num: the paragraph number
            pa_text: the text of the paragraph
            pa_raw_text: the raw text of the paragraph
            page: the page number
            par_inc_count: paragraph increment count
            pa_entities: a list of entities
        """

        self.type = "paragraph"
        self.f_name = f_name
        self.pa_num = pa_num
        self.pa_text = pa_text
        self.page_num = page
        self.par_inc_count = par_inc_count
        self.pa_raw_text = pa_raw_text
        self.pa_id = str(f_name) + "_" + str(par_inc_count)
        self.pa_entities = pa_entities


def extract_entities_dir(dir_path: str, dest: str):
    p = Path(dir_path).glob("**/*.json")
    files = [x for x in p if x.is_file()]

    for m_file in files:
        iss = Issuance(m_file, f_type="json")
        iss.extract_entities()
        iss.json_write(clean=False, out_dir=dest)


# TODO: refactor to use typing.NamedTuple or separate args
def single_process(data_inputs: t.Tuple[str, str, bool, str, bool, bool, int, bool]) -> None:
    """
    Args:
        data_inputs:tuple of the necessary data inputs

    Returns:
    """

    # TODO: refactor to use typing.NamedTuple or separate args
    (m_file, out_dir, clean, meta_data, skip_optional_ds, ocr_missing_doc, num_ocr_threads, ultra_simple) = data_inputs

    # Logging is not safe in multiprocessing thread. Especially if its going to a file
    # Directly printing to screen is a temporary solution here
    m_id = multiprocessing.current_process()

    # print(
    #     "%s - [INFO] - Processing: %s - Filename: %s"
    #     % (
    #         datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f'")[:-4],
    #         str(m_id),
    #         Path(m_file).name,
    #     )
    # )

    try:
        if not meta_data:
            iss = Issuance(m_file, ocr_missing_doc=ocr_missing_doc, num_ocr_threads=num_ocr_threads, ultra_simple=ultra_simple)
        else:

            loc_meta_path = Path(Path(meta_data) if Path(meta_data).is_dir() else Path(meta_data).parent,
                             Path(m_file).name + '.metadata')
            # loc_meta_path = Path(meta_data).with_name(Path(m_file).name + ".metadata")

            if loc_meta_path.exists():
                iss = Issuance(m_file, meta_data=loc_meta_path, ocr_missing_doc=ocr_missing_doc, num_ocr_threads=num_ocr_threads, ultra_simple=ultra_simple)
            else:
                iss = Issuance(m_file, ocr_missing_doc=ocr_missing_doc, num_ocr_threads=num_ocr_threads, ultra_simple=ultra_simple)

        iss.json_write(clean=clean, out_dir=out_dir, skip_optional_ds=skip_optional_ds, ultra_simple=ultra_simple)

    # TODO: catch this where failed files can be counted or increment shared counter (for mp)
    except (OCRError, UnparseableDocument) as e:
        print(e)
        print(
            "%s - [ERROR] - Failed Processing: %s - Filename: %s"
            % (
                datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f'")[:-4],
                str(m_id),
                Path(m_file).name,
            )
        )
        return

    # print(
    #     "%s - [INFO] - Finished Processing: %s - Filename: %s"
    #     % (
    #         datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f'")[:-4],
    #         str(m_id),
    #         Path(m_file).name,
    #     )
    # )


def process_dir(
        dir_path: str,
        out_dir: str = "./",
        clean: bool = False,
        meta_data: str = None,
        multiprocess: int = False,
        skip_optional_ds: bool = False,
        ocr_missing_doc: bool = False,
        num_ocr_threads: int = 2,
        ultra_simple: bool = False
):
    """
    Processes a directory of pdf files, returns corresponding Json files
    Args:
        dir_path: A source directory to be processed.
        out_dir: A destination directory to be processed
        clean: boolean to determine if text is to be cleaned or not. The text is cleaned from special characters and extra spaces
        meta_data: file path of metadata to be processed.
        multiprocess: Multiprocessing. Will take integer for number of cores
        skip_optional_ds: skip parsing of optional DS fields like entities
        ocr_missing_doc: OCR non-ocr'ed docs in place
        num_ocr_threads: Number of threads used for OCR (per doc)
    """

    p = Path(dir_path).glob("**/*")
    files = [x for x in p if x.is_file() and filetype.guess(str(x)) is not None and (
                filetype.guess(str(x)).mime == "pdf" or filetype.guess(str(x)) != "application/pdf")]

    # TODO: refactor to use list of typing.NamedTuple instead
    data_inputs = [(m_file, out_dir, clean, meta_data, skip_optional_ds, ocr_missing_doc, num_ocr_threads, ultra_simple) for m_file in
                   files]

    doc_logger = get_default_logger()
    doc_logger.info("Parsing Multiple Documents: %i", len(data_inputs))

    now = datetime.datetime.now()
    current_time = now.strftime("%H:%M:%S")
    print("Current Time =", current_time)

    if multiprocess != -1:
        if multiprocess == 0:
            pool = multiprocessing.Pool(processes=os.cpu_count(), maxtasksperchild=1)
        else:
            pool = multiprocessing.Pool(processes=int(multiprocess), maxtasksperchild=1)
        doc_logger.info("Processing pool: %s", str(pool))
        pool.map(single_process, data_inputs, 5)
    else:
        for item in data_inputs:
            single_process(item)

    now = datetime.datetime.now()
    current_time = now.strftime("%H:%M:%S")
    print("Current Time =", current_time)

    # TODO: actually track how many were successfully processed
    doc_logger.info("Documents parsed (or attempted): %i", len(data_inputs))
