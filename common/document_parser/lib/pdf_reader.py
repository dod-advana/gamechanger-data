import fitz


def get_fitz_doc_obj(f_name):
    doc = fitz.open(f_name)
    if doc.pageCount < 1:
        doc.close()
        raise Exception(
            f"Could not parse the doc, failed page count check: {f_name}")
    else:
        return doc
