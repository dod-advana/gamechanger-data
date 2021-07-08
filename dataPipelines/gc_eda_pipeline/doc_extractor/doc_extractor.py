from dataPipelines.gc_eda_pipeline.conf import Conf
from common.document_parser.parsers.eda_contract_search.parse import parse
import time

import os
from typing import Union
from pathlib import Path
from ocrmypdf import SubprocessOutputError
from common.utils.file_utils import is_pdf, is_ocr_pdf, is_encrypted_pdf
from dataPipelines.gc_ocr.utils import PDFOCR, OCRJobType
import traceback
from urllib3.exceptions import ProtocolError


def ocr_process(staging_folder: str, file: str, multiprocess: int, aws_s3_output_pdf_prefix: str,
                audit_rec: dict):

    # Download PDF file
    ocr_time_start = time.time()
    pdf_file_local_path = staging_folder + "/pdf/" + file

    get_ocr_file = False
    error_count = 0
    while not get_ocr_file and error_count < 10:
        try:
            saved_file = Conf.s3_utils.download_file(file=pdf_file_local_path, object_path=file)

            # OCR PDF if need
            is_pdf_file, is_ocr = pdf_ocr(file=file, staging_folder=staging_folder, multiprocess=multiprocess)

            # Copy PDF into S3
            pdf_file_s3_path = aws_s3_output_pdf_prefix + "/" + file
            Conf.s3_utils.upload_file(file=saved_file, object_name=pdf_file_s3_path)
            ocr_time_end = time.time()
            time_ocr = ocr_time_end - ocr_time_start
        except (ProtocolError, ConnectionError) as e:
            error_count += 1
            time.sleep(1)
        else:
            get_ocr_file = True

    audit_rec.update({"gc_path_s": pdf_file_s3_path, "is_ocr_b": is_ocr, "ocr_time_f": round(time_ocr, 4),
                      "modified_date_dt": int(time.time())})

    return is_pdf_file, pdf_file_local_path, pdf_file_s3_path


def extract_text(staging_folder: str, pdf_file_local_path: str, path: str, filename_without_ext: str,
                 aws_s3_json_prefix: str, audit_rec: dict):
    doc_time_start = time.time()
    ex_file_local_path = staging_folder + "/json/" + path + "/" + filename_without_ext + ".json"
    ex_file_s3_path = aws_s3_json_prefix + "/" + path + "/" + filename_without_ext + ".json"

    docparser(metadata_file_path=None, saved_file=pdf_file_local_path, staging_folder=staging_folder, path=path)
    if os.path.exists(ex_file_local_path):
        Conf.s3_utils.upload_file(file=ex_file_local_path,  object_name=ex_file_s3_path)
        is_extract_suc = True
    else:
        is_extract_suc = False

    doc_time_end = time.time()
    time_dp = doc_time_end - doc_time_start

    audit_rec.update({"json_path_s": ex_file_s3_path, "is_docparser_b": is_extract_suc,
                      "docparser_time_f": round(time_dp, 4), "modified_date_dt": int(time.time())})

    return ex_file_local_path, ex_file_s3_path, is_extract_suc


def docparser(metadata_file_path: str, saved_file: Union[str, Path], staging_folder: Union[str, Path], path: str) \
        -> bool:
    """
    OCR will be done outside of the docparser.
    """
    m_file = saved_file
    out_dir = staging_folder + "/json/" + path + "/"
    parse(f_name=m_file, meta_data=metadata_file_path, ocr_missing_doc=False, num_ocr_threads=1, out_dir=out_dir)
    return True


def pdf_ocr(file: str, staging_folder: str, multiprocess: int) -> (bool, bool):
    try:
        path, filename = os.path.split(file)
        is_ocr = False
        is_pdf_file = False
        if filename != "" and Conf.s3_utils.object_exists(object_path=file):
            saved_file = Conf.s3_utils.download_file(file=staging_folder + "/pdf/" + file, object_path=file)
            if not is_pdf(str(saved_file)):
                return is_pdf_file, is_ocr
            else:
                is_pdf_file = True
            try:
                if is_pdf(str(saved_file)) and not is_ocr_pdf(str(saved_file)) and not is_encrypted_pdf(str(saved_file)):
                    is_pdf_file = True
                    ocr = PDFOCR(
                        input_file=saved_file,
                        output_file=saved_file,
                        ocr_job_type=OCRJobType.SKIP_TEXT,
                        ignore_init_errors=True,
                        num_threads=multiprocess
                    )
                    try:
                        is_ocr = ocr.convert()
                    except SubprocessOutputError as e:
                        print(e)
                        is_ocr = False
            except Exception as ex:
                print(ex)
                is_ocr = False
            return is_pdf_file, is_ocr
    except RuntimeError as e:
        print(f"File does not look like a pdf file {saved_file}")
        traceback.print_exc()
        is_pdf_file = False
        is_ocr = False
        return is_pdf_file, is_ocr

    return is_pdf_file, is_ocr
