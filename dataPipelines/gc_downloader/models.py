from pathlib import Path
from dataPipelines.gc_crawler.data_model import Document
from typing import Union, Optional, Dict, Any
from .exceptions import CorruptedFile, CouldNotDownload, UnsupportedFileType
from enum import Enum
import json
import copy
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class EntryType(Enum):
    DOCUMENT = "document"
    DOC_METADATA = "doc_metadata"
    JOB_METADATA = "job_metadata"

class ManifestEntry:
    """Entry in the download manifest"""
    def __init__(self,
                 filename: str,
                 origin: str,
                 entrypoint: str,
                 version_hash: str,
                 md5_hash: str,
                 entry_type: Union[EntryType, str]):
        """
        :param filename: filename, as it appears in final output directory
        :param origin: most specific url known for retrieving related download item
        :param entrypoint: second most specific url for retrieving related download item (e.g. page url)
        :param version_hash: sha256 hex hash of information uniquely identifying this publication
        :param md5_hash: md5sum of the related file
        :param entry_type: manifest EntryType - 'document', 'metadata', etc.
        """
        self.entry_type = EntryType(entry_type)
        self.md5_hash = md5_hash
        self.version_hash = version_hash
        self.entrypoint = entrypoint
        self.origin = origin
        self.filename = filename

    def to_dict(self) -> Dict[str, Any]:
        """Plain dictionary representation"""
        return copy.deepcopy({
            **self.__dict__
        })

    def to_json(self) -> str:
        """Serialize to json string"""
        def _supplementary_json_encoder(o: object) -> object:
            """Handle conversion of objects that default json encoder can't handle"""
            if isinstance(o, Enum):
                return o.value
            else:
                return json.JSONEncoder().default(o)
        return json.dumps(self.to_dict(), default=_supplementary_json_encoder)

    @staticmethod
    def from_dict(obj_dict: Dict[Any, Any]) -> 'ManifestEntry':
        """Deserialize from plain dictionary"""
        _obj_dict = copy.deepcopy(obj_dict)  # avoid problems with arrays and other ref types
        return ManifestEntry(**_obj_dict)

    @staticmethod
    def from_json(serialized_obj: str) -> 'ManifestEntry':
        """Deserialize from json"""
        return ManifestEntry.from_dict(json.loads(serialized_obj))


class DownloadedDocument:
    """Model of a downloaded document"""
    def __init__(self,
                 document: Document,
                 downloaded_file_path: Union[str, Path],
                 origin: str,
                 entrypoint: str):
        """
        :param document: The Document obj corresponding to crawler output json
        :param downloaded_file_path: Local path to where document was downloaded
        :param origin: most specific url to to get the processed file, e.g. direct download url
        :param entrypoint: second most specific url to get the processed file, e.g. page url
        """
        self.document = document
        self.downloaded_file_path = downloaded_file_path
        self.origin = origin
        self.entrypoint = entrypoint


class ProcessedDocument:
    """Model of a fully processed document"""
    def __init__(self,
                 document: Document,
                 local_file_path: Union[str, Path],
                 metadata_file_path: Union[str, Path],
                 normalized_filename: str,
                 md5_hash: str,
                 origin: str,
                 entrypoint: str):
        """
        :param document: The Document obj corresponding to crawler output json
        :param local_file_path: actual local file path where processed document was placed
        :param metadata_file_path: Path to file containing json metadata, if any.
        :param normalized_filename: normalized filename - should be same as what's in local file
        :param md5_hash: md5hash sum of the processed file
        :param origin: most specific url to to get the processed file, e.g. direct download url
        :param entrypoint: second most specific url to get the processed file, e.g. page url
        path but collisions might happen, hence this attribute
        """
        self.document = document
        self.local_file_path = Path(local_file_path).resolve()
        self.metadata_file_path = metadata_file_path
        self.normalized_filename = normalized_filename or self.local_file_path.name
        self.md5_hash = md5_hash
        self.entrypoint = entrypoint
        self.origin = origin


class FailureReason(Enum):
    COULD_NOT_DOWNLOAD = 'could_not_download'
    CORRUPTED_FILE = 'corrupted_file'
    UNSUPPORTED_FILE = 'unsupported_file'
    WHO_KNOWS = 'who_knows'

    @staticmethod
    def from_exception(e: Exception) -> 'FailureReason':
        if isinstance(e, CouldNotDownload):
            return FailureReason.COULD_NOT_DOWNLOAD
        elif isinstance(e, CorruptedFile):
            return FailureReason.CORRUPTED_FILE
        elif isinstance(e, UnsupportedFileType):
            return FailureReason.UNSUPPORTED_FILE
        else:
            return FailureReason.WHO_KNOWS


class DeadDocument:
    """Model of document that failed to process for some reason"""
    def __init__(self, document: Document, failure_reason: Union[FailureReason, str] = FailureReason.WHO_KNOWS):
        """
        :param document: The Document obj corresponding to crawler output json
        """
        self.document = document
        self.failure_reason = FailureReason(failure_reason)

    def to_dict(self) -> Dict[str, Any]:
        """Plain dictionary representation"""
        return copy.deepcopy({
            **self.__dict__
        })

    def to_json(self) -> str:
        """Serialize to json string"""
        def _supplementary_json_encoder(o: object) -> object:
            """Handle conversion of objects that default json encoder can't handle"""
            if isinstance(o, Enum):
                return o.value
            if isinstance(o, Document):
                return o.to_json()
            else:
                return json.JSONEncoder().default(o)
        return json.dumps(self.to_dict(), default=_supplementary_json_encoder)

    @staticmethod
    def from_dict(obj_dict: Dict[Any, Any]) -> 'DeadDocument':
        """Deserialize from plain dictionary"""
        _obj_dict = copy.deepcopy(obj_dict)  # avoid problems with arrays and other ref types
        _obj_dict['document'] = Document.from_dict(_obj_dict['document'])
        return DeadDocument(**_obj_dict)

