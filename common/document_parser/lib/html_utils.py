from typing import AnyStr, IO, Union
from pathlib import Path

import bs4
from xhtml2pdf import pisa
from xhtml2pdf.context import pisaCSSBuilder
from xhtml2pdf.w3c.cssParser import CSSParser

def _remove_empty_attr(soup: bs4.BeautifulSoup, attr: str) -> None:
    """Removes the specified attribute from all tags if empty."""
    tags = soup.find_all(attrs={attr: True})
    for tag in tags:
        if tag[attr] == '':
            del tag[attr]

def _truncate_rowspan(soup: bs4.BeautifulSoup) -> None:
    """Ensure rowspan does not extend beyond end of tables."""
    tables = soup.find_all('table')
    for table in tables:
        rows = table.select('tr:not(:scope table tr)') # tr not nested inside another table
        max_row = len(rows)
        for i, row in enumerate(rows):
            cells = row.select('th:not(:scope table th), td:not(:scope table td)') # th/td not nested inside another table
            for cell in cells:
                if cell.has_attr('rowspan'):
                    rowspan = int(cell['rowspan'] or 1)
                    if rowspan > max_row - i:
                        cell['rowspan'] = f'{max_row - i}'


def clean_html_for_pdf(markup: Union[IO, AnyStr]) -> str:
    """Cleans known issues from html that prevent pdf generation."""
    soup = bs4.BeautifulSoup(markup, 'html5lib')

    # remove any empty rows (i.e. <tr> tags without any child <td> or <th> tags)
    rows = soup.find_all('tr')
    for row in rows:
        if row.find('td') is None and row.find('th') is None:
            row.decompose()

    # remove unparseable style attributes
    css_parser = CSSParser(pisaCSSBuilder(mediumSet=["all", "print", "pdf"]))
    styled_tags = soup.find_all(style=True)
    for tag in styled_tags:
        parsed_style = css_parser.parseInline(tag['style'])[0]
        if any(value is NotImplemented for value in parsed_style.values()):
            del tag['style']

    # remove problematic empty attributes
    _remove_empty_attr(soup, 'colspan')
    _remove_empty_attr(soup, 'rowspan')

    # cap overly large rowspan values
    _truncate_rowspan(soup)

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
        try:
            pisaStatus = pisa.CreatePDF(html, dest=pdf_file)
        except Exception:
            raise RuntimeError(f'unable to generate pdf from {filepath}')
    if pisaStatus.err:
        raise RuntimeError(f'unable to generate pdf from {filepath}')

    return str(pdf_path)
