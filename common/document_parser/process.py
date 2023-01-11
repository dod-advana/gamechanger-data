import multiprocessing
import typing
import os
from datetime import datetime
from pathlib import Path
import filetype
from collections import namedtuple

from . import get_default_logger

from dataPipelines.gc_ocr.utils import OCRError
from .lib.pdf_reader import PageCountParse

import time
import importlib

# Added for missed page fix
import concurrent.futures
from tqdm import tqdm
from common.utils.file_utils import is_pdf, is_ocr_pdf, is_encrypted_pdf, check_ocr_status_job_type
from ocrmypdf import SubprocessOutputError
from dataPipelines.gc_ocr.utils import PDFOCR, OCRJobType


class UnparseableDocument(Exception):
    """Document was unsuitable for parsing, for some reason"""
    pass

class PageCountCheck(Exception):
    """Could not parse the doc, failed page count check"""
    pass

def resolve_dynamic_func(func_path: str) -> typing.Callable[[dict], dict]:
    if '::' not in func_path:
        raise Exception(
            'Function name not found, use module.submodule::func_name syntax')

    (module_path, _, func_name) = func_path.partition('::')
    m = importlib.import_module(module_path)
    return getattr(m, func_name)


def resolve_dynamic_parser(parser_path: str) -> typing.Callable:
    """
    Args:
        parser_path: string of path::func or path to a parser module to load or to a config file that can be constructed into a parser

    Returns:
        callable function to run on parser_input
    """
    # entry point for future parser pipeline config file resolver
    # some like if parser is Path or str -> json read -> construct parsing pipeline and return it
    # if parser is dict -> construct parsing pipeline and return it

    if 'common.document_parser.parsers' not in parser_path:
        raise Exception(
            'parser_path not recognized, currently parsers must come from within common.document_parser.parsers like common.document_parser.parsers.policy_analytics.parse')

    func_name = 'parse'

    if '::' in parser_path:
        (module_path, _, func_name) = parser_path.partition('::')
        parser = importlib.import_module(module_path)
    else:
        parser = importlib.import_module(parser_path)

    try:
        return getattr(parser, func_name)
    except AttributeError:
        e = f"Function name {func_name} not found, 'parse' is the default or use module.submodule::func_name syntax"
        raise Exception(e)


def single_process(data_inputs: typing.Tuple[typing.Callable, str, str, bool, int, bool, str]) -> None:
    """
    Args:
        data_inputs: named tuple of kind "parser_input", the necessary data inputs
    Returns:
    """

    (parse_func,
     f_name,
     meta_data,
     ocr_missing_doc,
     num_ocr_threads,
     force_ocr,
     out_dir
     ) = data_inputs

    # Logging is not safe in multiprocessing thread. Especially if its going to a file
    # Directly printing to screen is a temporary solution here
    m_id = multiprocessing.current_process()

    print(
        "%s - [INFO] - Processing: %s - Filename: %s"
        % (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f'")[:-4],
            str(m_id),
            Path(f_name).name,
        )
    )

    try:
        if not meta_data:
            parse_func(f_name=f_name, meta_data=meta_data, ocr_missing_doc=ocr_missing_doc,
                       num_ocr_threads=num_ocr_threads, force_ocr=force_ocr, out_dir=out_dir)
        else:

            loc_meta_path = Path(Path(meta_data) if Path(meta_data).is_dir() else Path(meta_data).parent,
                                 Path(f_name).name + '.metadata')

            if loc_meta_path.exists():
                parse_func(f_name=f_name, meta_data=loc_meta_path, ocr_missing_doc=ocr_missing_doc, 
                           num_ocr_threads=num_ocr_threads, force_ocr=force_ocr, out_dir=out_dir)

            else:
                parse_func(f_name=f_name, meta_data=meta_data, ocr_missing_doc=ocr_missing_doc,
                           num_ocr_threads=num_ocr_threads, force_ocr=force_ocr, out_dir=out_dir)

    # TODO: catch this where failed files can be counted or increment shared counter (for mp)
    except (OCRError, UnparseableDocument, PageCountParse) as e:
        print(e)
        print(
            "%s - [ERROR] - Failed Processing: %s - Filename: %s"
            % (
                datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f'")[:-4],
                str(m_id),
                Path(f_name).name,
            )
        )
        return

    print(
        "%s - [INFO] - Finished Processing: %s - Filename: %s"
        % (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f'")[:-4],
            str(m_id),
            Path(f_name).name,
        )
    )


def process_dir(
        parse_func: typing.Callable,
        dir_path: str,
        out_dir: str = "./",
        meta_data: str = None,
        multiprocess: int = False,
        ocr_missing_doc: bool = False,
        force_ocr: bool = False,
        num_ocr_threads: int = 2,
        batch_size: int = 100
):
    """
    Processes a directory of pdf files, returns corresponding Json files
    Args:
        parse_func: Parsing function called on the data
        dir_path: A source directory to be processed.
        out_dir: A destination directory to be processed
        meta_data: file path of metadata to be processed.
        multiprocess: Multiprocessing. Will take integer for number of cores
        ocr_missing_doc: OCR non-ocr'ed docs in place
        num_ocr_threads: Number of threads used for OCR (per doc)
    """

    p = Path(dir_path).glob("**/*")
    files = [x for x in p if x.is_file() and (x.suffix.lower() in (".pdf", ".html", ".txt")
        or (filetype.guess(str(x)) is not None and (filetype.guess(str(x)).mime == "pdf" or filetype.guess(str(x)).mime == "application/pdf")))]
    data_inputs = [(parse_func, f_name, str(f_name)+'.metadata', ocr_missing_doc,
                    num_ocr_threads, force_ocr, out_dir) for f_name in files]

    doc_logger = get_default_logger()
    doc_logger.info("Parsing Multiple Documents: %i", len(data_inputs))

    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    print("Current Time =", current_time)

    if multiprocess != -1:
        # begin = time.time()
        if multiprocess == 0:
            pool = multiprocessing.Pool(
                processes=os.cpu_count(), maxtasksperchild=1)
        else:
            pool = multiprocessing.Pool(
                processes=int(multiprocess), maxtasksperchild=1)
        doc_logger.info("Processing pool: %s", str(pool))
        
        # ReOCR PDF if need (ex: page is missing)
        start_ocr_time = datetime.now()
        start_ocr_time_display = start_ocr_time.strftime("%H:%M:%S")
        print("Start reOCR Time =", start_ocr_time_display)


        # How many elements each list should have # work around with issue on queue being over filled
        # using list comprehension
        process_list = [data_inputs[i * batch_size:(i + 1) * batch_size] for i in range((len(data_inputs) + batch_size - 1) // batch_size)]
        
        total_num_files = len(data_inputs)
        reocr_count = 0
        for item_process in tqdm(process_list):
            with concurrent.futures.ProcessPoolExecutor(max_workers=5) as executor:
                results = [executor.submit(check_ocr_status_job_type, data[1]) for data in item_process]
                for index, fut in enumerate(concurrent.futures.as_completed(results)):
                    if not isinstance(fut, type(None)):
                        if fut.result() is not None:
                            ocrd_pdf = fut.result().get('successful_ocr')
                            if is_pdf(str(item_process[index][1])) and not ocrd_pdf and not is_encrypted_pdf(str(item_process[index][1])):
                                reocr_count+=1
                                kwargs = {#"deskew": True if ocr_job_type == OCRJobType.FORCE_OCR else False,
                                    #"rotate_pages": True,
                                    #"use_threads":True,
                                    "bad_pages": fut.result().get('bad_page_nums')}
                                try:
                                    print(f"[OCR] Attempt reOCR of pages {kwargs.get('bad_pages')}")
                                    # TODO: This is not multi threaded -- we want to multithread and batch process!!!!!
                                    ocr = PDFOCR(
                                        input_file=item_process[index][1],
                                        output_file=item_process[index][1],
                                        ocr_job_type=fut.result().get('ocr_job_type'),
                                        ignore_init_errors=True,
                                        num_threads=num_ocr_threads # default=2
                                    )
                                    try:
                                        is_ocr = ocr.convert(**kwargs)
                                    except SubprocessOutputError as e:
                                        print(e)
                                        is_ocr = False
                                except Exception as ex:
                                    print(ex)
                                    is_ocr = False
        
        end_ocr_time = datetime.now()
        end_ocr_time_dispaly = end_ocr_time.strftime("%H:%M:%S")
        total_ocr_time = end_ocr_time - start_ocr_time
        print("End  reOCR  Time =", end_ocr_time_dispaly)
        print("Total OCR Time:", total_ocr_time)
        print(f"Count of documents reOCRed / total: {reocr_count} / {total_num_files}")
        # Process files
        pool.map(single_process, data_inputs, batch_size)
        # diff = time.time() - begin
        # print('MP total: ', diff)
        # print('MP avg', diff / (len(data_inputs) + 0.0001))
    else:
        # times = []
        for item in data_inputs:
            # start = time.time()
            single_process(item)
            # end = time.time()
            # diff = end - start
            # print('single runtime: ', diff)
            # times.append(diff)

        # total = sum(times)
        # print('total: ', total)
        # average = total / (len(times) + 0.0001)
        # print('average: ', average)

    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    print("Current Time =", current_time)

    # TODO: actually track how many were successfully processed
    doc_logger.info("Documents parsed (or attempted): %i", len(data_inputs))