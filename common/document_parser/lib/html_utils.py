from common.utils.file_utils import is_pdf, is_ocr_pdf
from .ocr import get_ocr_filename
from xhtml2pdf import pisa


def get_html_filename(f_name) -> str:

    if not is_pdf(str(f_name)):
        source_html = open(f_name, "r")
        content = source_html.read()
        source_html.close()
        tmp_pdf = open(f_name.replace('.html', '.pdf'), "w+b")
        pisa_status = pisa.CreatePDF(content, dest = tmp_pdf)
        tmp_pdf.close()
        pdf_name = get_ocr_filename(tmp_pdf)

    return pdf_name

