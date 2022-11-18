"""
OCR PDF extractor
Uses the ocrmypdf application which can be installed through 
pip install ocrmypdf
Reference: https://ocrmypdf.readthedocs.io/en/latest/installation.html
"""

from pathlib import Path
import typing as t
from common.utils.file_utils import is_pdf, is_ocr_pdf, is_encrypted_pdf
import ocrmypdf
import sys
from enum import Enum
import subprocess as sub


class OCRJobType(Enum):
    """
    :param NORMAL: only OCR if not already OCR'ed
    :param SKIP_TEXT: OCR any non-OCR'ed text in a PDF, but keep what was already OCR'ed
    :param REDO_OCR: re-OCR any text except vector text
    :param FORCE_OCR: Convert PDF pages to images and OCR everything, whether already OCR'ed or not
    """
    NORMAL='normal'
    SKIP_TEXT='skip-text'
    REDO_OCR='redo-ocr'
    FORCE_OCR='force-ocr'


class OCRError(Exception):
    """Error thrown by the OCR Job"""
    pass

class NotPDFError(OCRError):
    """When file is not a pdf"""
    pass


class EncryptedPDFError(OCRError):
    """When pdf is encrypted"""
    pass


class PreviouslyOCRError(OCRError):
    """When pdf is already OCRed"""
    pass


class PDFOCR:
    def __init__(self,
                 input_file: t.Union[str, Path],
                 output_file: t.Optional[t.Union[str, Path]] = None,
                 ocr_job_type: t.Union[OCRJobType, str] = OCRJobType.NORMAL,
                 output_extension: t.Optional[t.AnyStr] = None,
                 overwrite_output: bool = True,
                 ignore_init_errors: bool = True,
                 show_progress_bar: bool = False,
                 num_threads: t.Optional[int] = None,
                 force_ocr: bool = False
                 ):
        """PDF OCR Util
        :param input_file: Input pdf file path
        :param output_file: Output pdf file path (optional, can be same as input)
        :param output_extension: Special ext suffix for the output file
        :param ocr_job_type: OCR job type ('normal','skip-text','redo-ocr','force-ocr')
        :param ignore_init_errors: Don't raise errors related to job type
        :param show_progress_bar: Show progress bar during conversion
        """

        self.input_file = Path(input_file).resolve()
        self.output_file = Path(output_file or self.input_file).resolve()
        # cleaning up output ext str
        if output_extension is not None:
            output_extension_str = str(output_extension).strip()
            if output_extension_str:
                output_extension_str = (
                    output_extension_str if output_extension_str.startswith('.')
                    else '.' + output_extension_str
                )
                self.output_extension = output_extension_str
                self.output_file = self.output_file.with_suffix(self.output_extension)

        self.job_type = OCRJobType(ocr_job_type)
        self.show_progress_bar = show_progress_bar
        self.num_threads = num_threads if (num_threads is None or num_threads > 0) else None

        # checks
        if self.output_file.exists() and not overwrite_output:
            raise FileExistsError(f"Output file already exists: {self.output_file!s}")

        if not is_pdf(self.input_file):
            e = NotPDFError(f"Given file is not a pdf: {self.input_file!s}")
            if not ignore_init_errors:
                print(e)
            else:
                raise e
        elif is_encrypted_pdf(self.input_file):
            e = EncryptedPDFError(f"Give file is an encrypted pdf: {self.input_file!s}")
            if not ignore_init_errors:
                print(e)
            else:
                raise e
        elif is_ocr_pdf(self.input_file) and not self.job_type in [OCRJobType.FORCE_OCR,OCRJobType.REDO_OCR]:
            e = PreviouslyOCRError(f"Given file is already OCR'ed: {self.input_file!s}")
            if not ignore_init_errors:
                print(e)
            else:
                raise e

    def convert(self, raise_error: bool = False, **kwargs) -> bool:
        print(f"[INFO] OCR'ing file {self.input_file!s}, writing output to {self.output_file!s}", file=sys.stderr)
        exit_code = ocrmypdf.ocr(
            input_file=self.input_file,
            output_file=self.output_file,
            skip_text=True if self.job_type == OCRJobType.SKIP_TEXT else None,
            redo_ocr=True if self.job_type == OCRJobType.REDO_OCR else None,
            force_ocr=True if self.job_type == OCRJobType.FORCE_OCR else None,
            progress_bar=self.show_progress_bar,
            jobs=self.num_threads,
            deskew = kwargs.get("deskew",False),
            rotate_pages = kwargs.get("rotate_pages",False)
        )

        is_successful = exit_code == ocrmypdf.ExitCode.ok
        if raise_error and not is_successful:
            raise OCRError(f"[ERROR] Could not OCR '{self.input_file.name}'")

        return is_successful

    def convert_in_subprocess(self, raise_error: bool = False) -> bool:
        """Run in a subprocess, supports non-daemonic MP pools"""
        print(f"[INFO] OCR'ing [In Subprocess] file {self.input_file!s}, writing output to {self.output_file!s}", file=sys.stderr)
        process = sub.run(
            [
                'ocrmypdf',
                *[p for p in
                    [
                        {
                            OCRJobType.SKIP_TEXT: '--skip-text',
                            OCRJobType.REDO_OCR: '--redo-ocr',
                            OCRJobType.FORCE_OCR: '--force-ocr'
                        }.get(self.job_type)
                        
                    ] if p
                ],
                f'--jobs={self.num_threads}',
                str(self.input_file),
                str(self.output_file)
            ]
        )

        is_successful = process.returncode == 0
        if raise_error and not is_successful:
            raise OCRError(f"[ERROR] Could not OCR '{self.input_file.name}'")

        return is_successful