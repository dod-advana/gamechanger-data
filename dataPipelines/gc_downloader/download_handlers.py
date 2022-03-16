from abc import abstractmethod
from dataPipelines.gc_crawler.data_model import Document
from dataPipelines.gc_downloader.models import DownloadedDocument, ProcessedDocument, DeadDocument, FailureReason
from .doc_utils import unzip_docs_as_needed, download_doc, download_doc_with_driver
from .file_utils import safe_move_file
from pathlib import Path
from typing import Optional, Union, Iterable, List
import tempfile
import copy
import re
from .file_utils import md5_for_file
from .string_utils import normalize_string
from abc import ABC
from .exceptions import CouldNotDownload, UnsupportedFileType, CorruptedFile, ProcessingError
from .file_checkers import is_valid_pdf
from selenium import webdriver
from selenium.common.exceptions import WebDriverException


# TODO: Move document filtering logic to download handlers
# TODO: See if setting up generalized Job Handlers makes sense given other validation activities
# TODO: Detect corrupted files and raise appropriate exceptions (partly done for pdfs)
# TODO: Construct DeadDocument based on appropriate exceptions


class DownloadHandler(ABC):
    """Base class for handlers that perform oft. source-dependent tasks on downloaded docs.
        This includes such things as unzipping files, filtering out junk files from archives,
        renaming documents to something more palatable for the end users, etc.
    """
    driver = None

    @classmethod
    @abstractmethod
    def update_driver(cls, driver: webdriver.Chrome)-> bool:
        """Returns boolean whether or not the driver variable is updated

            :param driver: webdriver
            :return: true or false whether the driver was updated
        """
        pass

    @classmethod
    @abstractmethod
    def normalize_filename(cls, ddoc: DownloadedDocument) -> str:
        """Returns normalized filename given context DownloadedDocument information

        :param ddoc: Single DownloadedDocument
        :return: Normalized filename string corresponding to given DownloadedDocument
        """
        pass

    @classmethod
    @abstractmethod
    def unpack_if_needed_and_rename(cls,
                                    ddoc: DownloadedDocument,
                                    output_dir: Union[str, Path]) -> List[DownloadedDocument]:
        """Unpacks file, if appropriate, and appropriately renames the file.

        :param ddoc: Single DownloadedDocument
        :param output_dir: Path to directory where unpacked/renamed docs should be placed
        :return: List of downloaded documents
        """
        pass

    @classmethod
    @abstractmethod
    def process_doc(cls, doc: Document, output_dir: Union[str, Path]) -> List[ProcessedDocument]:
        """Process given Document and output final file to output directory

        :param doc: Single Document object, presumably read from crawler JSON output
        :param output_dir: Path to directory where processed doc should land
        :return: Iterable of ProcessedDocument(s)
        :raises: ProcessingError
        """
        pass

    @classmethod
    @abstractmethod
    def process_all_docs(cls,
                         docs: Iterable[Document],
                         output_dir: Union[str, Path]) -> Iterable[ProcessedDocument]:
        """Process given DownloadedDocuments and output final files to output directory

        :param docs: Iterable of Document objects, presumably read from crawler JSON output
        :param output_dir: Path to directory where all processed docs should land
        :return: Iterable of ProcessedDocument(s)
        """
        pass


class DefaultDownloadHandler(DownloadHandler):
    """Default download handler"""

    @classmethod
    def update_driver(cls, driver: webdriver.Chrome)-> bool:
        return False

    @classmethod
    def normalize_filename(cls, ddoc: DownloadedDocument) -> str:
        return normalize_string(ddoc.document.doc_name) + Path(ddoc.downloaded_file_path).suffix.lower()

    @classmethod
    def unpack_if_needed_and_rename(cls,
                                    ddoc: DownloadedDocument,
                                    output_dir: Union[str, Path]) -> List[DownloadedDocument]:
        output_dir_path = Path(output_dir).resolve()

        with tempfile.TemporaryDirectory() as temp_dir:
            unpacked_renamed_docs = []
            ddocs = unzip_docs_as_needed(ddoc=ddoc, output_dir=temp_dir)

            for ddoc in ddocs:
                desired_filename = cls.normalize_filename(ddoc)
                desired_path = Path(output_dir_path, desired_filename)
                output_file_path = safe_move_file(
                    file_path=ddoc.downloaded_file_path,
                    output_path=desired_path
                )

                new_ddoc = copy.deepcopy(ddoc)
                new_ddoc.downloaded_file_path = output_file_path

                unpacked_renamed_docs.append(new_ddoc)

        return unpacked_renamed_docs

    @classmethod
    def process_doc(cls, doc: Document, output_dir: Union[str, Path]) -> List[ProcessedDocument]:

        with tempfile.TemporaryDirectory() as temp_dir_path:
            try:
                ddoc = download_doc(doc=doc, output_dir=temp_dir_path)
            except CouldNotDownload as e:
                # for transparency's sake...
                print(e)
                raise e

            # TODO: Pull out validation checks into separate abstract class method
            # TODO: Create check dispatcher based on supported file extensions (a-la get_appropriate_file_handler())
            unpacked_renamed_docs = cls.unpack_if_needed_and_rename(ddoc=ddoc, output_dir=output_dir)
            for ddoc in unpacked_renamed_docs:
                if not is_valid_pdf(ddoc.downloaded_file_path):
                    # no need to keep file around if it's corrupt
                    if ddoc.downloaded_file_path.exists():
                        ddoc.downloaded_file_path.unlink()
                    raise CorruptedFile(ddoc.downloaded_file_path)

        processed_docs = []
        for ddoc in unpacked_renamed_docs:

            # recording metadata
            metadata_filename = f"{ddoc.downloaded_file_path.name}.metadata"  # type: ignore
            metadata_path = Path(ddoc.downloaded_file_path.parent, metadata_filename)  # type: ignore
            with metadata_path.open(mode="w") as fd:
                fd.write(ddoc.document.to_json() + "\n")

            # form processed doc
            processed_doc = ProcessedDocument(
                document=ddoc.document,
                local_file_path=ddoc.downloaded_file_path,
                metadata_file_path=metadata_path,
                normalized_filename=cls.normalize_filename(ddoc),
                md5_hash=md5_for_file(ddoc.downloaded_file_path),
                origin=ddoc.origin,
                entrypoint=ddoc.entrypoint
            )

            processed_docs.append(processed_doc)

        return processed_docs

    @classmethod
    def process_all_docs(cls,
                         docs: Iterable[Document],
                         output_dir: Union[str, Path]) -> Iterable[Union[ProcessedDocument, DeadDocument]]:
        for doc in docs:
            try:
                for pdoc in cls.process_doc(doc=doc, output_dir=output_dir):
                    print(f"Processed {pdoc.normalized_filename} -- {pdoc.local_file_path}")
                    yield pdoc
            except ProcessingError as e:
                print(f"Failed to process {doc.doc_name}")
                yield DeadDocument(
                    document=doc,
                    failure_reason=FailureReason.from_exception(e)
                )


class USCodeDownloadHandler(DefaultDownloadHandler):
    """US Code download handler"""

    @classmethod
    def normalize_filename(cls, ddoc: DownloadedDocument) -> str:
        file_basename = ddoc.downloaded_file_path.name  # type: ignore
        file_extension = ddoc.downloaded_file_path.suffix.lower()  # type: ignore

        # chapter and section info to tell apart different part files, like for Title 42
        chapters_matcher = re.match(
            pattern=r".*?(ch\d+[a-zA-Z]?to\d+[a-zA-Z]?).*",
            string=file_basename,
            flags=re.IGNORECASE,
        )

        sections_matcher = re.match(
            pattern=r".*?(Secs\d+[a-zA-Z]?to\d+[a-zA-Z]?).*",
            string=file_basename,
            flags=re.IGNORECASE,
        )

        filename_suffix = (
                (chapters_matcher.group(1) if chapters_matcher else "")
                + ("_" + sections_matcher.group(1) if sections_matcher else "")
        )

        doc_base_name = ddoc.document.doc_type + " " + str(ddoc.document.doc_num)
        if ddoc.document.doc_title.lower() == 'appendix':
            doc_base_name += " - Appendix"

        full_filename = (
                normalize_string(doc_base_name)
                + ((" - " + filename_suffix) if filename_suffix else "")
                + file_extension
        )

        return full_filename


class DriverDownloadHandler(DefaultDownloadHandler):
    """Download handler for crawlers that require selenium"""

    @classmethod
    def update_driver(cls, driver: webdriver.chrome.webdriver):
        cls.driver = driver

    def __init__(self, driver):
        self.update_driver(driver)

    @classmethod
    def process_doc(cls, doc: Document, output_dir: Union[str, Path]) -> List[ProcessedDocument]:
        try:
            ddoc = download_doc_with_driver(doc=doc, output_dir=output_dir, driver=cls.driver)
        except CouldNotDownload as e:
            # for transparency's sake...
            print(e)
            raise e

        # TODO: Pull out validation checks into separate abstract class method
        # TODO: Create check dispatcher based on supported file extensions (a-la get_appropriate_file_handler())
        unpacked_renamed_docs = cls.unpack_if_needed_and_rename(ddoc=ddoc, output_dir=output_dir)
        for ddoc in unpacked_renamed_docs:
            if not is_valid_pdf(ddoc.downloaded_file_path):
                # no need to keep file around if it's corrupt
                if ddoc.downloaded_file_path.exists():
                    ddoc.downloaded_file_path.unlink()
                raise CorruptedFile(ddoc.downloaded_file_path)

        processed_docs = []
        for ddoc in unpacked_renamed_docs:
            # recording metadata
            metadata_filename = f"{ddoc.downloaded_file_path.name}.metadata"  # type: ignore
            metadata_path = Path(ddoc.downloaded_file_path.parent, metadata_filename)  # type: ignore
            with metadata_path.open(mode="w") as fd:
                fd.write(ddoc.document.to_json() + "\n")

            # form processed doc
            processed_doc = ProcessedDocument(
                document=ddoc.document,
                local_file_path=ddoc.downloaded_file_path,
                metadata_file_path=metadata_path,
                normalized_filename=cls.normalize_filename(ddoc),
                md5_hash=md5_for_file(ddoc.downloaded_file_path),
                origin=ddoc.origin,
                entrypoint=ddoc.entrypoint
            )

            processed_docs.append(processed_doc)

        return processed_docs


def get_appropriate_file_handler(doc: Union[Document, DownloadedDocument, ProcessedDocument], driver: webdriver.Chrome) -> DownloadHandler:
    """Get file handler appropriate for given ddoc"""
    if isinstance(doc, (ProcessedDocument, DownloadedDocument)):
        crawler_used = doc.document.crawler_used
    else:
        crawler_used = doc.crawler_used

    return {
        'us_code': USCodeDownloadHandler(),
        'army_pubs': DriverDownloadHandler(driver),
        'nato_stanag': DriverDownloadHandler(driver)
    }.get(crawler_used, DefaultDownloadHandler())


def process_all_docs(
        docs: Iterable[Document],
        output_dir: Union[str, Path],
        driver: webdriver.Chrome,
        echo: bool = True) -> Iterable[Union[ProcessedDocument, DeadDocument]]:
    """Process all documents
    :param docs: Iterable of Document(s)
    :param output_dir: Final ouutput dir for downloaded/processed documents
    :param driver: Chrome webdriver session
    :param echo: Flag - echo file info as they're being processed, or not.
    :return: Iterable returning either ProcessedDocument(s) or DeadDocument(s), depending on
    whether doc was successfully processed or not
    """

    for doc in docs:
        if echo:
            print(f"Processing document: {doc.doc_name}")
        handler = get_appropriate_file_handler(doc=doc, driver=driver)

        for pdoc in handler.process_all_docs(docs=[doc], output_dir=output_dir):
            yield pdoc