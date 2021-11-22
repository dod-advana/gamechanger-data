import typing as t
from pathlib import Path
import fitz
import os
import PyPDF2
from PyPDF2.utils import PdfReadError


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


def is_ocr_pdf(file: t.Union[Path, str]) -> bool:
    """Check if given pdf file is OCR'ed"""
    file_path = Path(file).resolve()
    try:
        with fitz.open(str(file_path)) as doc:
            for page_num in range(doc.pageCount):
                if doc.getPageText(page_num).strip():
                    return True
            return False
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
