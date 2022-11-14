import typing as t
from pathlib import Path
import fitz
import os
import PyPDF2
from PyPDF2.utils import PdfReadError
from dataPipelines.gc_ocr.utils import OCRJobType


def walk_files(src: t.Union[Path, str]) -> t.Iterable[Path]:
    src_path = Path(src)
    if not src_path.is_dir():
        raise ValueError(f"Given src is not a dir {src!s}")
    for p in src_path.rglob("*"):
        if p.is_dir():
            continue
        yield p


def ensure_dir(path: t.Union[Path, str]) -> Path:
    """Ensure given directory path exists"""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def is_pdf(file: t.Union[Path, str]) -> bool:
    """Check if given file is a readable PDF file"""
    file_path = Path(file).resolve()

    try:
        doc = fitz.open(file_path)
    except RuntimeError as e:
        if 'no objects found' in e.args:
            return False
    except:
        return False
    finally:
        doc.close()

    return True


def is_ocr_pdf(file: t.Union[Path, str], error_char_threshold=.2) -> bool:
    """Check if given pdf file is OCR'ed"""
    file_path = Path(file).resolve()
    try:
        with fitz.open(str(file_path)) as doc:
            for page_num in range(doc.pageCount):
                page_text = doc.getPageText(page_num).strip()
                # if there is ocr'd text present
                if page_text:
                    # check to see if the OCR font (or char encodings) are problematic, and the PDF does need OCR
                    # character 65533 is the 'replace'/'unknown' character. If the percentage of error characters is
                    # greater than the error_char_threshold, the document requires "
                    if [ord(char) for char in page_text].count(65533) / len(page_text) > error_char_threshold:
                        return False
                    # This document contains well suited OCR already
                    else:
                        return True
            return False
    except Exception as e:
        print(f"Unexpected error while trying to open {file_path}")
        print(e)
        return False

def check_ocr_status_job_type(file: t.Union[Path, str], error_char_threshold=.2):
    """Check if given pdf file is OCR'ed"""
    file_path = Path(file).resolve()
    try:
        with fitz.open(str(file_path)) as doc:
            total_pages = doc.pageCount
            missing_text_page_count = 0
            for page_num in range(total_pages):
                page_text = doc.getPageText(page_num).strip()
                # if there is ocr'd text present
                if page_text:
                    # check to see if the OCR font (or char encodings) are problematic, and the PDF does need OCR
                    # character 65533 is the 'replace'/'unknown' character. If the percentage of error characters is
                    # greater than the error_char_threshold, the document requires "
                    if [ord(char) for char in page_text].count(65533) / len(page_text) > error_char_threshold:
                        return False, OCRJobType.FORCE_OCR
                else:
                    missing_text_page_count+=1
            # if there are missing text pages, and none of the pages contain erroneous glyph/text, then redo OCR - else
            # skip OCRing all together
            if missing_text_page_count>0:
                return False, OCRJobType.REDO_OCR
            else:
                return True, OCRJobType.SKIP_TEXT
    except Exception as e:
        print(f"Unexpected error while trying to open {file_path}")
        print(e)
        return False

def is_encrypted_pdf(file: t.Union[Path, str]) -> bool:
    """Check if pdf file is encrypted"""
    file_path = Path(file).resolve()

    try:
        pdf_reader = PyPDF2.PdfFileReader(str(file_path))
        return pdf_reader.isEncrypted
    except PdfReadError as e:
        print(f"PdfReadError error while trying to open {file_path.name}")
        print(e)
        return True  # err on a side of caution
    except Exception as e:
        print(f"Unexpected error while trying to open {file_path.name}")
        print(e)
        return True  # err on a side of caution
