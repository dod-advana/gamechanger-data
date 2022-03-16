from typing import Iterable
from pathlib import Path
from typing import Union, Any, Dict, Optional
import json
from .models import ProcessedDocument, DeadDocument, ManifestEntry, EntryType
from .file_utils import md5_for_file


def get_downloaded_version_hashes(manifest: Union[Path, str]) -> Iterable[str]:
    """Get version_hashes for all documents at given download manifest path

    :param manifest: Path to existing manifest of downloaded/processed docs
    :return: Iterable of document version_hash'es from the manifest
    """
    manifest_path = Path(manifest).resolve()

    with manifest_path.open(mode="r") as f:
        for line in f.readlines():
            if not line.strip():
                continue

            jdoc = json.loads(line)
            if jdoc['entry_type'] == EntryType.DOCUMENT.value:
                yield jdoc['version_hash']


def gen_doc_manifest_entry(pdoc: ProcessedDocument) -> ManifestEntry:
    """Generate ManifestEntry for given ProcessedDocument
    :param pdoc: Single ProcessedDocument
    :return: ManifestEntry corresponding to 'pdoc'
    """
    return ManifestEntry(
        filename=pdoc.local_file_path.name,
        origin=pdoc.origin,
        entrypoint=pdoc.entrypoint,
        version_hash=pdoc.document.version_hash,
        md5_hash=pdoc.md5_hash,
        entry_type=EntryType.DOCUMENT
    )


def gen_doc_metadata_manifest_entry(pdoc: ProcessedDocument) -> Optional[ManifestEntry]:
    """Generate ManifestEntry for metadata associated with given ProcessedDocument
    :param pdoc: Single ProcessedDocument
    :return: ManifestEntry for metadata corresponding to 'pdoc', if any.
    """
    if not pdoc.metadata_file_path:
        return None

    md5sum = md5_for_file(pdoc.metadata_file_path)
    return ManifestEntry(
        filename=pdoc.metadata_file_path.name,  # type: ignore
        origin=f"metadata://{pdoc.local_file_path.name}",
        entrypoint=f"metadata://{pdoc.local_file_path.name}",
        version_hash=md5sum,
        md5_hash=md5sum,
        entry_type=EntryType.DOC_METADATA
    )


def gen_job_metadata_manifest_entry(file: Union[str, Path]) -> ManifestEntry:
    """Generate ManifestEntry corresponding to a metadata file pertinent to job as a whole
    :param file: path to said file
    :return: corresponding ManifestEntry
    """
    file_path = Path(file).resolve()

    md5sum = md5_for_file(file_path)
    return ManifestEntry(
        filename=file_path.name,
        origin="metadata://",
        entrypoint="metadata://",
        version_hash=md5sum,
        md5_hash=md5sum,
        entry_type=EntryType.JOB_METADATA
    )


def record_metadata_file_in_manifest(file: Union[str, Path], manifest: Union[Path, str]) -> None:
    """ Append new entry to existing manifest for given job metadata file.

    :param file: path to arbitrary job metadata file (e.g. log, etc.)
    :param manifest: path to overall job manifest.json file
    :return: None - modifies manifest as side-effect
    """
    manifest_path = Path(manifest).resolve()

    entry = gen_job_metadata_manifest_entry(file)
    with manifest_path.open(mode="a") as fd:
        fd.write(entry.to_json() + "\n")


def record_dead_doc(dead_doc: DeadDocument, dead_queue: Union[Path, str]) -> None:
    """Append given dead document in the dead queue file
    :param dead_doc: some DeadDocument
    :param dead_queue: path to dead queue file
    :return: None - modified dead queue file as a side-effect
    """
    dead_queue_path = Path(dead_queue).resolve()
    with dead_queue_path.open(mode="a") as fd:
        fd.write(dead_doc.to_json() + "\n")


def record_doc_and_metadata_in_manifest(pdoc: ProcessedDocument, manifest: Union[Path, str]) -> None:
    """Append JSON manifest records about the document and its' metadata in the overall manifest

    :param pdoc: Single ProcessedDocument
    :param manifest: Path to the overall manifest
    :return: None - modifies manifest as side-effect
    """
    doc_manifest_entry = gen_doc_manifest_entry(pdoc)
    metadata_manifest_entry = gen_doc_metadata_manifest_entry(pdoc)

    manifest_path = Path(manifest).resolve()

    with manifest_path.open(mode="a") as fd:
        fd.write(doc_manifest_entry.to_json() + "\n")
        if metadata_manifest_entry:
            fd.write(metadata_manifest_entry.to_json() + "\n")