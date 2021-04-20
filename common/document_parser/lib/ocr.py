from dataPipelines.gc_ocr.utils import PDFOCR, OCRJobType, OCRError
from common.utils.file_utils import is_pdf, is_ocr_pdf, is_encrypted_pdf


def get_ocr_filename(f_name, num_ocr_threads=2) -> str:
    if not is_ocr_pdf(str(f_name)) and not is_encrypted_pdf(str(f_name)):
        ocr = PDFOCR(
            input_file=f_name,
            output_file=f_name,
            # best to force OCR if the earlier OCR checks failed anyway
            ocr_job_type=OCRJobType.FORCE_OCR,
            ignore_init_errors=True,
            num_threads=num_ocr_threads
        )
        ocr.convert_in_subprocess(raise_error=True)
        f_name = str(ocr.output_file)
    return f_name
