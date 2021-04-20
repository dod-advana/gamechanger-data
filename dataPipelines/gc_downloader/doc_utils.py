from dataPipelines.gc_crawler.data_model import Document, DownloadableItem
from .models import DownloadedDocument, ProcessedDocument
from pathlib import Path
from typing import Dict, Iterable, Optional, Any, Union, List
import copy
import tempfile
from .file_utils import safe_move_file, unzip_all
from .download_utils import download_file, download_file_with_driver
import json
from .manifest_utils import get_downloaded_version_hashes
from .exceptions import CouldNotDownload
from selenium import webdriver


def get_pdf_downloadable_item(doc: Document) -> Optional[DownloadableItem]:
    """Get pdf downloadable item corresponding to doc"""
    return next((i for i in doc.downloadable_items if i.doc_type.lower() == 'pdf'), None)


def read_docs_from_file(file_path: Path) -> Iterable[Document]:
    """Iterate over input json docs from given file path"""
    with file_path.open(mode="r") as f:
        for json_str in f.readlines():
            if not json_str.strip():
                continue
            try:
                doc = Document.from_dict(json.loads(json_str))
                yield doc  # because otherwise error is thrown outside the method
            except json.decoder.JSONDecodeError:
                print("Encountered JSON decode error while parsing crawler output.")
                continue


def filter_out_cac_pubs(docs: Iterable[Document]) -> Iterable[Document]:
    """Iterate over input docs, filtering out cac pubs"""
    for doc in docs:
        if doc.cac_login_required:
            continue
        else:
            yield doc


def filter_out_non_pdf_docs(docs: Iterable[Document]) -> Iterable[Document]:
    """Filters out non-pdf docs"""
    for doc in docs:
        if not get_pdf_downloadable_item(doc):
            continue
        yield doc


def filter_out_already_downloaded_docs(
        docs: Iterable[Document],
        previous_manifest: Optional[Union[str, Path]] = None) -> Iterable[Document]:
    """Filter out docs that are in the old manifest"""

    previous_manifest_path = (
        Path(previous_manifest).resolve()
        if previous_manifest
        else None
    )

    version_hashes = (
        list(get_downloaded_version_hashes(previous_manifest_path))  # type: ignore
        if previous_manifest
        else []
    )

    for doc in docs:
        if doc.version_hash in version_hashes:
            continue
        else:
            yield doc


def download_doc(doc: Document, output_dir: Union[Path, str]) -> DownloadedDocument:
    """Download doc to given base_dir"""
    item = get_pdf_downloadable_item(doc)
    if not item:
        print(f"Couldn't find a suitable downloadable item for doc {doc.doc_name}")
        return None

    output_dir_path = Path(output_dir).resolve()

    try:
        downloaded_file = download_file(
            url=item.web_url,
            output_dir=output_dir_path
        )
    except CouldNotDownload as e:
        # for transparency's sake...
        raise e

    return DownloadedDocument(
        document=doc,
        downloaded_file_path=str(downloaded_file.resolve()),
        origin=item.web_url,
        entrypoint=doc.source_page_url
    )

def download_doc_with_driver(doc: Document, output_dir: Union[Path, str], driver: webdriver.Chrome) -> DownloadedDocument:
    """Download doc to given base_dir"""
    item = get_pdf_downloadable_item(doc)
    if not item:
        print(f"Couldn't find a suitable downloadable item for doc {doc.doc_name}")
        return None

    output_dir_path = Path(output_dir).resolve()

    try:
        downloaded_file = download_file_with_driver(
            url=item.web_url,
            output_dir=output_dir_path,
            driver=driver
        )
    except CouldNotDownload as e:
        # for transparency's sake...
        raise e

    return DownloadedDocument(
        document=doc,
        downloaded_file_path=str(downloaded_file.resolve()),
        origin=item.web_url,
        entrypoint=doc.source_page_url
    )

def unzip_docs_as_needed(ddoc: DownloadedDocument, output_dir: Union[Path, str]) -> List[DownloadedDocument]:
    """Handles zipped/packaged download artifacts by expanding them into their individual components

    :param ddoc: DownloadedDocument obj
    :param output_dir: Directory where files, unzipped or not, should be placed
    :return: iterable of Downloaded documents, len > 1 for bundles
    """

    file = Path(ddoc.downloaded_file_path).resolve()

    # TODO: create set of recursive unzip methods for other archive types and a dispatcher
    if not file.suffix.lower() == ".zip":
        new_path = safe_move_file(file_path=ddoc.downloaded_file_path, output_path=output_dir)
        new_ddoc = copy.deepcopy(ddoc)
        new_ddoc.downloaded_file_path = new_path
        return [new_ddoc]

    try:
        # unzip & move
        temp_dir = tempfile.TemporaryDirectory()
        unzipped_files = unzip_all(zip_file=file.resolve(), output_dir=temp_dir.name)

        # TODO: Extend for non-pdf docs (trickier than it seems, there can be junk/manifest files)
        unzipped_pdf_files = [f for f in unzipped_files if f.suffix.lower() == ".pdf"]
        if not unzipped_pdf_files:
            raise RuntimeError(f"Tried to unzip {file.name}, but could not find any expected files inside")

        final_ddocs = []
        for pdf_file in unzipped_pdf_files:
            new_ddoc = copy.deepcopy(ddoc)
            new_path = safe_move_file(file_path=pdf_file, output_path=output_dir)
            new_ddoc.downloaded_file_path = new_path

            final_ddocs.append(new_ddoc)
    finally:
        temp_dir.cleanup()

    return final_ddocs
