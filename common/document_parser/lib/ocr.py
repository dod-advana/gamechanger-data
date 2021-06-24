from dataPipelines.gc_ocr.utils import PDFOCR, OCRJobType, OCRError
from pathlib import Path
import filetype
from common.utils.file_utils import is_pdf, is_ocr_pdf, is_encrypted_pdf


def is_pdf_file(f_name) -> bool:
    if Path(f_name).suffix == ".pdf" or (filetype.guess(str(f_name)) is not None and
         (filetype.guess(str(f_name)).mime == "pdf" or
          filetype.guess(str(f_name)).mime == "application/pdf")):
        return True
    else:
        return False

def get_ocr_filename(f_name, num_ocr_threads=2,force_ocr=False) -> str:
    if is_pdf_file(f_name):
        # if not is_ocr_pdf(str(f_name)) and not is_encrypted_pdf(str(f_name)):
        encrypted_file = is_encrypted_pdf(str(f_name))
        is_ocr_pdf_bool = is_ocr_pdf(str(f_name))
        if (force_ocr or not is_ocr_pdf_bool) and not encrypted_file:
            ocr = PDFOCR(
                input_file=f_name,
                output_file=f_name,
                # best to force OCR if the earlier OCR checks failed anyway
                ocr_job_type=OCRJobType.FORCE_OCR,
                ignore_init_errors=True,
                num_threads=num_ocr_threads,
                force_ocr=force_ocr
            )
            ocr.convert_in_subprocess(raise_error=True)
            f_name = str(ocr.output_file)

    return f_name
