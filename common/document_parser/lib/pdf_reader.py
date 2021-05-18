import fitz

class PageCountParse(Exception):
    """Could not parse the doc, failed page count check"""
    pass

def get_fitz_doc_obj(f_name):
    doc = fitz.open(f_name)
    if doc.pageCount < 1:
        doc.close()
        raise PageCountParse(
            f"Could not parse the doc, failed page count check: {f_name}")
    else:
        return doc
