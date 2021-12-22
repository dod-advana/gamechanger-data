from typing import AnyStr, IO, Union
from pathlib import Path

import bs4
from xhtml2pdf import pisa

def clean_html_for_pdf(markup: Union[IO, AnyStr]) -> str:
    """Cleans known issues from html that prevent pdf generation."""
    soup = bs4.BeautifulSoup(markup, 'html5lib')

    # remove any empty rows (i.e. <tr> tags without any child <td> or <th> tags)
    rows = soup.find_all('tr')
    for row in rows:
        if row.find('td') is None and row.find('th') is None:
            row.decompose()

    return str(soup)

def convert_html_to_pdf(filepath: Union[Path, str]) -> str:
    """Creates pdf for parsing."""
    filepath = Path(filepath)
    if filepath.suffix == '.pdf':
        return str(filepath)
    with open(filepath, 'rb') as html_file:
        html = clean_html_for_pdf(html_file)
    pdf_path = filepath.with_suffix('.pdf')
    with open(pdf_path, 'w+b') as pdf_file:
        pisaStatus = pisa.CreatePDF(html, dest=pdf_file)
    if pisaStatus.err:
        raise RuntimeError(f'unable to generate pdf from {filepath}')

    return str(pdf_path)
