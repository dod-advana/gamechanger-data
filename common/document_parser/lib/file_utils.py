from pathlib import Path
from typing import Union

from common.document_parser.lib.html_utils import convert_html_file_to_pdf, convert_html_to_pdf, convert_text_to_html
from common.document_parser.lib.reading_in import read_plain_text


def coerce_file_to_pdf(filepath: Union[Path, str]) -> str:
    """Attempts to convert the given file to a pdf and returns the pdf filepath."""
    filepath = Path(filepath)
    filetype = filepath.suffix
    if filetype == '.pdf' or filetype == '.PDF':
        return str(filepath)
    elif filetype == '.html':
        return convert_html_file_to_pdf(filepath)
    elif filetype == '.txt':
        text = read_plain_text(filepath)
        html = convert_text_to_html(text)
        return convert_html_to_pdf(filepath, html)
    else:
        raise ValueError(f'unsupported filetype {filetype}')
