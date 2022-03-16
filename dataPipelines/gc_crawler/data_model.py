# -*- coding: utf-8 -*-
"""
gc_crawler.data_model
-----------------
Main data types that power gc_crawler
"""

from typing import List, Dict, Optional, Any
import json
from datetime import datetime
from .utils import dict_to_sha256_hex_digest, get_fqdn_from_web_url
import copy

#####
# OUTPUT DATA MODEL
#####


class DownloadableItem:
    """Downloadable Item associated with some Document
      :param doc_type: document's ultimate (i.e. uncompressed) file type; e.g. "pdf"
      :param web_url: web url from which the document can be downloaded
      :param compression_type: compression type of the document, e.g. "tgz"
    """

    def __init__(self,
                 doc_type: str,
                 web_url: str,
                 compression_type: Optional[str] = None):
        self.doc_type = doc_type
        self.web_url = web_url
        self.compression_type = compression_type

    def to_dict(self) -> Dict[str, Any]:
        """Plain dictionary representation"""
        return copy.deepcopy(self.__dict__)

    @staticmethod
    def from_dict(obj_dict: Dict[Any, Any]) -> 'DownloadableItem':
        """Deserialize DownloadableItem object from plain dictionary"""
        _obj_dict = copy.deepcopy(obj_dict)  # avoid problems with arrays and other ref types
        return DownloadableItem(**_obj_dict)


class Document:
    """Downloadable Document
    :param doc_name: document name (typically derived)
    :param doc_title: full document title, often same as document name
    :param doc_num: document number - pubs can typically be identified by combination of this and doc_title
    :param doc_type: document type, e.g. "title" for US Code Titles
    :param publication_date: date of publication e.g. "08/18/2020"
    :param cac_login_required: whether or not the document requires CAC login for download
    :param crawler_used: name of crawler used to scrape data
    :param source_page_url: page url where info about this doc was found, e.g. https://library.gov/main?page=1"
    :param downloadable_items: downloadable items related to this document
    :param version_hash_raw_data: raw data used to calculate the version hash
    :param access_timestamp: utc timestamp of when doc was discovered.
    :param source_fqdn: data source FQDN, e.g. "library.gov"
    :param version_hash: version hash, presumably based on version_hash_raw_data (should normally be left blank)
    """

    def __init__(
        self,
        doc_name: str,
        doc_title: str,
        doc_num: str,
        doc_type: str,
        publication_date: str,
        cac_login_required: bool,
        crawler_used: str,
        source_page_url: str,
        downloadable_items: List[DownloadableItem],
        version_hash_raw_data: Dict[str, Any],
        original_publication_date: Optional[str] = None,
        access_timestamp: datetime = datetime.now(),
        source_fqdn: Optional[str] = None,
        version_hash: Optional[str] = None
    ):
        self.doc_name = doc_name
        self.doc_title = doc_title
        self.doc_num = doc_num
        self.doc_type = doc_type
        self.original_publication_date = original_publication_date or publication_date
        self.publication_date = publication_date
        self.cac_login_required = cac_login_required
        self.crawler_used = crawler_used
        self.source_page_url = source_page_url
        self.downloadable_items = downloadable_items
        self.version_hash_raw_data = version_hash_raw_data
        self.access_timestamp = access_timestamp
        self.source_fqdn = source_fqdn or get_fqdn_from_web_url(self.source_page_url)
        self.version_hash = version_hash or dict_to_sha256_hex_digest(version_hash_raw_data)

    def to_dict(self) -> Dict[str, Any]:
        """Plain dictionary representation"""
        return copy.deepcopy({
            **self.__dict__,
            'downloadable_items': [i.to_dict() for i in self.downloadable_items]
        })

    def to_json(self) -> str:
        """Serialize to json string"""

        def _supplementary_json_encoder(o: object) -> object:
            """Handle conversion of objects that default json encoder can't handle"""
            if isinstance(o, datetime):
                return datetime.strftime(o, '%Y-%m-%d %H:%M:%S.%f')
            elif isinstance(o, DownloadableItem):
                return o.to_dict()
            else:
                return json.JSONEncoder().default(o)

        return json.dumps(self.to_dict(), default=_supplementary_json_encoder)

    @staticmethod
    def from_dict(obj_dict: Dict[Any, Any]) -> 'Document':
        """Deserialize Document object from plain dictionary"""
        _obj_dict = copy.deepcopy(obj_dict)  # avoid problems with arrays and other ref types

        downloadable_items = [
            DownloadableItem.from_dict(item) for item in _obj_dict['downloadable_items']
        ]

        _obj_dict['downloadable_items'] = downloadable_items
        if not isinstance(_obj_dict['access_timestamp'], datetime):
            _obj_dict['access_timestamp'] = datetime.strptime(
                _obj_dict['access_timestamp'], '%Y-%m-%d %H:%M:%S.%f'
            )

        return Document(**_obj_dict)

    @staticmethod
    def from_json(serialized_obj: str) -> 'Document':
        """Deserialize Document object from json"""
        return Document.from_dict(json.loads(serialized_obj))
