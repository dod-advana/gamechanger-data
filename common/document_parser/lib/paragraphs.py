from common.document_parser.lib.document import Document, FieldNames


def add_paragraphs(doc_dict):
    """Add and populate the paragraphs field of doc_dict. 
    
    See Document.make_paragraphs_dict() for fields added.

    Args:
        doc_dict (dict)

    Returns:
        dict: The updated dictionary.
    """
    document = Document(doc_dict)
    document.set_field(FieldNames.PARAGRAPHS, document.make_paragraph_dicts())

    return document.doc_dict

