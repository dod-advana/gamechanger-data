import click

from .utils import PDFOCR, OCRJobType
from common.utils.file_utils import is_pdf, is_ocr_pdf
import typing as t

####
# CLI
####


@click.group(name='ocr')
def cli():
    """OCR CLI"""
    pass


@cli.command(name="is-ocr")
@click.option(
    '-f',
    '--filename',
    help="",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, resolve_path=True),
    required=True,
)
@click.option(
    '-q',
    '--quiet',
    help="Don't echo ocr status, just return exit code",
    is_flag=True
)
def is_ocr(filename: str, quiet: bool) -> None:
    """Check if file is an OCR'ed PDF"""
    status = is_pdf(filename) and is_ocr_pdf(filename)
    if not status:
        if not quiet:
            print(f"{filename} :: is not OCR'ed PDF")
        exit(1)
    else:
        if not quiet:
            print(f"{filename} :: is OCR'ed PDF")
        exit(0)


@cli.command(name='process')
@click.option(
    '-i',
    '--input-file',
    help="Path to input file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, resolve_path=True),
    required=True,
)
@click.option(
    '-o',
    '--output-file',
    help="Path to output file, can be omitted to ocr file in place.",
    required=False,
    default=None
)
@click.option(
    '-t',
    '--job-type',
    help="Should we always ocr the document even it it already contains selectable text",
    type=click.Choice([e.value for e in OCRJobType]),
    default=OCRJobType.NORMAL.value
)
@click.option(
    '-e',
    '--output-extension',
    help="Output extension, e.g. .pdf.ocr to replace normal .pdf extension",
    type=str,
    default=None
)
@click.option(
    '--no-overwrite',
    help="Don't overwrite file at output if one already exists",
    is_flag=True
)
@click.option(
    '--no-progress',
    help="Don't show progress bar",
    is_flag=True
)
def process(
        input_file: str,
        output_file: t.Optional[str],
        job_type: str,
        output_extension: t.Optional[str],
        no_overwrite: bool,
        no_progress: bool) -> None:
    """Run OCR"""
    ocr_mgr = PDFOCR(
        input_file=input_file,
        output_file=output_file,
        ocr_job_type=job_type,
        output_extension=output_extension,
        overwrite_output=not no_overwrite,
        ignore_init_errors=True,
        show_progress_bar=not no_progress
    )
    success = ocr_mgr.convert()
    if not success:
        exit(1)
