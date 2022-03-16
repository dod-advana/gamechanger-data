import click
from textwrap import dedent
from pathlib import Path
from typing import Optional
from .file_utils import pad_empty_file
from .doc_utils import (
    read_docs_from_file, filter_out_cac_pubs,
    filter_out_already_downloaded_docs, filter_out_non_pdf_docs
)
from .download_handlers import process_all_docs
from .manifest_utils import (
    record_doc_and_metadata_in_manifest, record_metadata_file_in_manifest,
    record_dead_doc
)
from .models import ProcessedDocument, DeadDocument
from .config import Config
from dataPipelines.gc_crawler.utils import close_driver_windows_and_quit
####
# CLI
####


@click.group(context_settings=dict(max_content_width=120))
def cli():
    pass


@cli.command(name='download')
@click.option(
    '--input-json',
    help='JSON input file',
    type=click.Path(
        exists=True,
        file_okay=True,
        dir_okay=False,
        resolve_path=True,
        allow_dash=False
    ),
    required=True
)
@click.option(
    '--output-dir',
    help='Output directory for downloaded files',
    type=click.Path(
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True
    ),
    required=True
)
@click.option(
    '--previous-manifest',
    help='JSON manifest of previously downloaded files',
    type=click.Path(
        exists=True,
        file_okay=True,
        dir_okay=False,
        resolve_path=True
    ),
    required=False
)
@click.option(
    '--new-manifest',
    help='JSON manifest of newly downloaded files',
    type=click.Path(
        exists=False,
        file_okay=True,
        dir_okay=False,
        resolve_path=True
    ),
    required=False
)
@click.option(
    '--dead-queue',
    help='Log of JSONs for docs that failed to process for some reason',
    type=click.Path(
        exists=False,
        file_okay=True,
        dir_okay=False,
        resolve_path=True
    ),
    required=False
)
def download(input_json: str,
             output_dir: str,
             previous_manifest: Optional[str],
             new_manifest: Optional[str],
             dead_queue: Optional[str]) -> None:
    """Download & process files corresponding to json entries output by crawlers."""

    input_json_path = Path(input_json).resolve()
    output_dir_path = Path(output_dir).resolve()
    previous_manifest_path = (
        Path(previous_manifest).resolve()
        if previous_manifest
        else None
    )
    new_manifest_path = (
        Path(new_manifest).resolve()
        if new_manifest
        else Path(output_dir_path, Config.default_manifest_name)
    )
    dead_queue_path = (
        Path(dead_queue).resolve()
        if dead_queue
        else Path(output_dir_path, Config.default_dead_queue_name)
    )

    # TODO: remove after troubleshooting
    # purge_dir(str(output_dir_path))

    print(dedent("""
     ---                       ---
    --- DOWNLOADING PUBLICATIONS ---
     ---                       ---
    """))

    print(dedent(f"""
    -- ARGS/VARS --

    input_json_path is {input_json_path!s}
    output_dir_path is {output_dir_path!s}
    previous_manifest_path is {previous_manifest_path!s}
    new_manifest_path is {new_manifest_path!s}
    dead_queue_path is {dead_queue_path!s}
    """))

    print("-- RUNNING --\n")

    # make sure manifest.json file exists, even if nothing gets downloaded
    new_manifest_path.touch(exist_ok=True)
    pad_empty_file(new_manifest_path)

    # same for DLQ
    dead_queue_path.touch(exist_ok=True)
    pad_empty_file(dead_queue_path)

    # read docs
    input_docs = list(read_docs_from_file(input_json_path))

    # TODO: move out document filtering logic into download handlers so unsupported docs can be recorded in dead queue
    # skip what was downloaded
    docs_sans_downloaded = list(filter_out_already_downloaded_docs(
                docs=input_docs,
                previous_manifest=previous_manifest_path
    ))
    # skip cac pubs
    docs_sans_cac_pubs = list(filter_out_cac_pubs(docs_sans_downloaded))
    # skip pubs with no pdf download items
    docs_sans_non_pdf_pubs = list(filter_out_non_pdf_docs(docs_sans_cac_pubs))

    # get web driver in case we're processing selenium sources
    driver = Config.get_driver(output_dir_path)
    processed_docs = process_all_docs(
        docs=docs_sans_non_pdf_pubs,
        output_dir=output_dir_path,
        driver=driver,
        echo=True
    )

    for doc in processed_docs:
        if isinstance(doc, ProcessedDocument):
            record_doc_and_metadata_in_manifest(
                pdoc=doc,
                manifest=new_manifest_path
            )
        elif isinstance(doc, DeadDocument):
            record_dead_doc(
                dead_doc=doc,
                dead_queue=dead_queue_path
            )
        else:
            raise RuntimeError("Unexpected code branch. Check process_all_docs() impl.")

    # close the web driver windows/process
    close_driver_windows_and_quit(driver)

    # make sure DLQ file is reflected in overall manifest
    record_metadata_file_in_manifest(file=dead_queue_path, manifest=new_manifest_path)

    print(f"\nFull manifest of successfully processed files is at {new_manifest_path!s}")
    print(f"\nDocuments that failed to process are reflected in {dead_queue_path!s}")
    print("\n-- DONE --\n")


@cli.command(name='add-to-manifest')
@click.option(
    '--file',
    help='some metadata file',
    type=click.Path(
        exists=True,
        file_okay=True,
        dir_okay=False,
        resolve_path=True,
        allow_dash=False
    ),
    required=True
)
@click.option(
    '--manifest',
    help='Download job JSON manifest',
    type=click.Path(
        exists=False,
        file_okay=True,
        dir_okay=False,
        resolve_path=True
    ),
    required=True
)
def add_to_manifest(file: str, manifest: str):
    """Add another file to the manifest"""
    file_path = Path(file).resolve()
    manifest_path = Path(manifest).resolve()

    if file_path.parent != manifest_path.parent:
        raise ValueError("File and manifest must be in the same directory")

    record_metadata_file_in_manifest(file=file_path, manifest=manifest_path)
    print(f'Recorded misc metadata file "{file_path.name}" in the overall job manifest.')
