import mimetypes
from pathlib import Path
from typing import IO, AnyStr, Union

import bs4
from w3lib.url import url_query_cleaner
from xhtml2pdf import pisa
from xhtml2pdf.context import pisaCSSBuilder
from xhtml2pdf.default import DEFAULT_CSS as XHTML2PDF_DEFAULT_CSS
from xhtml2pdf.w3c.cssParser import CSSParser

_DEFAULT_CSS = f'{XHTML2PDF_DEFAULT_CSS} table {{ -pdf-keep-in-frame-mode: shrink; }}'
"""Default CSS to use when rendering html to pdf.

Xhtml2pdf is unable to break table cells across pdf pages so will error if a cell is larger
than a page. To work around this we shrink tables to fit within a page. This can result in 
very small tables which are not suitable for human consumption but are fine for machine text
extraction.
"""

_BLACK_PIXEL_DATA_URL = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAYAAABytg0kAAAAAXNSR0IArs4c6QAAAAlwSFlzAAAWJQAAFiUBSVIk8AAAABNJREFUCB1jZGBg+A/EDEwgAgQADigBA//q6GsAAAAASUVORK5CYII%3D'
"""Data URL containing a png with a single black pixel."""

def _link_callback(uri: str, rel: str) -> str:
    """Replace default link loading in xhtml2pdf.
    
    We don't want the pdf generation process to actually attempt to hit the network or
    filesystem so we return a placeholder data URL for links that appear to be images
    otherwise we simply return an empty string so that nothing is loaded."""
    uri = url_query_cleaner(uri)
    type_, _ = mimetypes.guess_type(uri)
    if type_ and type_.startswith('image/'):
        return _BLACK_PIXEL_DATA_URL
    else:
        return ''

def _remove_empty_rows(soup: bs4.BeautifulSoup) -> None:
    """Remove any empty rows (i.e. <tr> tags without any child <td> or <th> tags)."""
    rows = soup.find_all('tr')
    for row in rows:
        if row.find('td') is None and row.find('th') is None:
            row.decompose()

def _remove_unparseable_style_attrs(soup: bs4.BeautifulSoup) -> None:
    """Removes unparseable style attributes."""
    css_parser = CSSParser(pisaCSSBuilder(mediumSet=["all", "print", "pdf"]))
    styled_tags = soup.find_all(style=True)
    for tag in styled_tags:
        parsed_style = css_parser.parseInline(tag['style'])[0]
        if any(value is NotImplemented for value in parsed_style.values()):
            del tag['style']

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


def _remove_nav_bar(soup: bs4.BeautifulSoup) -> None:
    """Remove navbar and links - specifically for MARADMIN, SAMM"""
    soup_search_args = [
        ('header', {"class": "navbar"}), # MARADMIN
        ('div', {"class": "clearfix header-inside"}), # SAMM
        ('div', {"class": "mobile-nav"}), # MARADMIN
        ('footer', {}), # MARADMIN
    ]
    header_tags = []
    for name, attrs in soup_search_args:
        header_tags += soup.findAll(name=name, attrs=attrs)
    for header_tag in header_tags:
        header_tag.decompose()
        del header_tag

def _remove_header_href(soup: bs4.BeautifulSoup) -> None:
    """Remove any a tag with the class 'visually-hidden. . .  etc' """
    a_tag = soup.find('a', class_='visually-hidden focusable skip-link') # Targetting SAMM Chapters
    if a_tag is not None:
        a_tag.decompose()      

def clean_html_for_pdf(markup: Union[IO, AnyStr]) -> str:
    """Cleans known issues from html that prevent pdf generation."""
    soup = bs4.BeautifulSoup(markup, 'html5lib')

    # remove empty rows
    _remove_empty_rows(soup)

    # remove unparseable style attributes
    _remove_unparseable_style_attrs(soup)

    # remove problematic empty attributes
    _remove_empty_attr(soup, 'colspan')
    _remove_empty_attr(soup, 'rowspan')

    # cap overly large rowspan values
    _truncate_rowspan(soup)

    _remove_nav_bar(soup)

    _remove_header_href(soup)

    return str(soup)

def convert_html_to_pdf(filepath: Union[Path, str], html: str) -> str:
    """Creates pdf file for parsing from an html string."""
    filepath = Path(filepath)
    pdf_path = filepath.with_suffix('.pdf')
    with open(pdf_path, 'w+b') as pdf_file:
        try:
            pisaStatus = pisa.CreatePDF(html, dest=pdf_file, link_callback=_link_callback, default_css=_DEFAULT_CSS)
        except Exception:
            raise RuntimeError(f'unable to generate pdf from {filepath}')
    if pisaStatus.err:
        raise RuntimeError(f'unable to generate pdf from {filepath}')
    return str(pdf_path)
    
def convert_html_file_to_pdf(filepath: Union[Path, str]) -> str:
    """Creates pdf file for parsing from an html file."""
    with open(filepath, 'rb') as html_file:
        html = clean_html_for_pdf(html_file)
    return convert_html_to_pdf(filepath, html)

def convert_text_to_html(text: str) -> str:
    """Returns equivalent html containing the provided text."""
    lines = text.splitlines()

    soup = bs4.BeautifulSoup('<html><body></body></html>', 'html5lib')
    body = soup.body
    for line in lines:
        body.append(line)
        br = soup.new_tag('br')
        body.append(br)

    html = str(soup)
    return html


