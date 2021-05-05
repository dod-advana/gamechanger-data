from common.utils.file_utils import is_pdf, is_ocr_pdf
from .ocr import get_ocr_filename
from xhtml2pdf import pisa

def get_html_filename(f_name) -> str:
    """
    creates pdf for parsing 
    """
    tmp_pdf = open(str(f_name).replace('.html', '.pdf'), "w+b")
    if str(f_name).endswith("html"):
        source_html = open(str(f_name), "r")
        content = source_html.read()
        source_html.close()
        pisaStatus = pisa.CreatePDF(content, dest=tmp_pdf)
        tmp_pdf.close()

    return str(f_name).replace('.html', '.pdf')

