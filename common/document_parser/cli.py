import click
from common.document_parser import validators
import pandas as pd
from pathlib import Path
from . import get_default_logger
import sys
import resource
import platform
import shutil


@click.group()
def cli():
    """
    Document parsing tool
    """
    pass


def json_to_csv(source:str, destination:str) -> None:
    """
    Converts Json file to csv
    Args:
        source: A source directory to be processed.
        destination:A destination directory to be processed

    """
    # delays load of ml models to speed up cli
    from common.document_parser import Document

    doc_logger = get_default_logger()

    if Path(source).is_file():
        iss_list = []
        iss = Document.Issuance(Path(source), f_type="json")
        iss_list.append(iss.to_dict(full_text=False, clean=False))
        df = pd.DataFrame(iss_list)
        df.reset_index(drop=True, inplace=True)
        if destination == '-':
            df.to_csv(sys.stdout)
        else:
            df.to_csv(destination)
    else:
        p = Path(source).glob("**/*.json")
        files = [x for x in p if x.is_file()]
        iss_list = []
        for m_file in files:
            doc_logger.info("Processing: %s", Path(m_file).name)
            iss = Document.Issuance(m_file, f_type="json")
            iss_list.append(iss.to_dict(full_text=False, clean=False))
        df = pd.DataFrame(iss_list)
        df.reset_index(drop=True, inplace=True)
        if destination == '-':
            df.to_csv(sys.stdout)
        else:
            df.to_csv(destination)


def pdf_to_json(
        clean:bool,
        source:str,
        destination:str,
        verify:bool=False,
        metadata:str=None,
        multiprocess:int=-1,
        skip_optional_ds:bool=False,
        ocr_missing_doc:bool=False,
        num_ocr_threads:int=2,
        ultra_simple:bool=False
) -> None:
    """
    Converts input pdf file to json
    Args:
        clean: boolean to determine if text is to be cleaned or not. The text is cleaned from special characters and extra spaces
        source: A source directory to be processed.
        destination: A destination directory to be processed
        verify: Boolean to determine if output jsons are to be verified vs a json schema
        metadata: file path of metadata to be processed.
        multiprocess: Multiprocessing. Will take integer for number of cores,
        skip_optional_ds: Skip generating certain DS fields like entities
        ocr_missing_doc: OCR non-OCR'ed files
        num_ocr_threads: Number of threads to use for OCR (per file)
    """
    # delays load of ml models to speed up cli
    from common.document_parser import Document

    doc_logger = get_default_logger()

    if Path(source).is_file():
        doc_logger.info("Parsing Single Document")
        doc = Document.Issuance(source, meta_data=metadata, ocr_missing_doc=ocr_missing_doc, num_ocr_threads=num_ocr_threads)
        doc.json_write(clean=clean, out_dir=destination)
    else:
        Document.process_dir(
            dir_path=source,
            out_dir=destination,
            clean=clean,
            meta_data=metadata,
            multiprocess=multiprocess,
            skip_optional_ds=skip_optional_ds,
            ocr_missing_doc=ocr_missing_doc,
            num_ocr_threads=num_ocr_threads,
            ultra_simple=ultra_simple
        )
    if verify:
        verified = validators.verify(destination)
        if verified:
            print("Jsons are verified")
        else:
            print("Jsons do not match the schema")
            exit(1)


@cli.command(name="validate-json")
@click.option(
    '-s',
    '--source',
    help='A source directory to be processed.',
    type=click.Path(resolve_path=True, exists=True),
    required=True,
)
def validate_json(source:str) -> None:
    """
    Takes in a directory of Jsons, or one specific json, and verifies vs a json schema
    Args:
        source:A source directory to be processed.

    """
    result = validators.verify(source)
    if result:
        print("Jsons have been validated")
    else:
        print("Jsons do not match the schema")


@cli.command(name="json-to-csv")
@click.option(
    '-s', '--source', help='A source directory to be processed.', required=True
)
@click.option(
    '-d', '--destination', help='Output file path for resulting csv .', default='-'
)
def json_to_csv_cmd_wrapper(source:str, destination:str) -> None:
    """Convert JSON files in a dir to CSV"""
    json_to_csv(source, destination)


@cli.command(name="pdf-to-json")
@click.option(
    '-c',
    '--clean',
    is_flag=True,
    help='The text is cleaned from special characters and extra spaces',
    default=False,
)
@click.option(
    '-v',
    '--verify',
    is_flag=True,
    help='verify the created json files vs a json schema',
    default=False,
)
@click.option(
    '-s',
    '--source',
    help='A source directory to be processed.',
    type=click.Path(resolve_path=True, exists=True),
    required=True,
)
@click.option(
    '-d',
    '--destination',
    required=True,
    type=click.Path(exists=True, file_okay=False, dir_okay=True, resolve_path=True),
    help='A destination directory to be processed.',
)
@click.option(
    '-m',
    '--metadata',
    help='Meta data from ingestion can be passed here as a json file, '
         + 'or pass same directory as pdfs if meta data is available there. '
         + 'Looks for matching *.metadata if directory',
    type=click.Path(exists=True, file_okay=True, dir_okay=True, resolve_path=True),
    default=None,
)

@click.option(
    '-p',
    '--multiprocess',
    required=False,
    default=-1,
    type=int,
    help="Multiprocessing. If treated like flag, will do max cores available. \
                if treated like option will take integer for number of cores.",
)
@click.option(
    '-w',
    '--ocr-missing-doc',
    help="If the file is not OCR, it will OCR the file. Default is to do nothing.",
    is_flag=True
)
@click.option(
    '-x',
    '--skip_optional_ds',
    required=False,
    is_flag=True,
    help='Optional data science steps like entity extraction are skipped',
    default=False,
)
@click.option(
    '-u',
    '--ultra_simple',
    required=False,
    is_flag=True,
    help='Optional most steps are skipped',
    default=False,
)
@click.option(
    '-z',
    '--memory_percentage',
    required=False,
    default=0.8,
    type=float,
    help="Limited the maximum memory usage.",
)
@click.option(
    '--num-ocr-threads',
    default=2,
    type=int,
    help="Number of threads to use for OCR (per file)"
)
def pdf_to_json_cmd_wrapper(
        clean: bool,
        source: str,
        destination: str,
        metadata: str,
        multiprocess: int,
        verify: bool,
        memory_percentage: float,
        skip_optional_ds: bool,
        ocr_missing_doc: bool,
        num_ocr_threads: int,
        ultra_simple: bool) -> None:
    """Parse OCR'ed PDF files into JSON schema"""
    if platform.system() == "Linux":
        memory_limit(memory_percentage)

    pdf_to_json(
        clean=clean,
        source=source,
        destination=destination,
        verify=verify,
        metadata=metadata,
        multiprocess=multiprocess,
        skip_optional_ds=skip_optional_ds,
        ocr_missing_doc=ocr_missing_doc,
        num_ocr_threads=num_ocr_threads,
        ultra_simple=ultra_simple)


def memory_limit(memory_percentage: float):
    """
    limits the percentage of memory usage allowed
    Args:
        memory_percentage: the percent allowed as a float
    """
    soft, hard = resource.getrlimit(resource.RLIMIT_AS)
    print("Memory Hard Limit: " + str(hard) + " Soft Limit: " + str(soft) + " Maximum of percentage of memory use: " + str(memory_percentage))
    resource.setrlimit(resource.RLIMIT_AS, (get_memory() * 1024 * memory_percentage, hard))


def get_memory():
    """
    returns the free memory available
    """
    with open('/proc/meminfo', 'r') as mem:
        free_memory = 0
        for i in mem:
            sline = i.split()
            if str(sline[0]) in ('MemFree:', 'Buffers:', 'Cached:'):
                free_memory += int(sline[1])
    print("____________________ " + str(free_memory) + "____________________")
    return free_memory
