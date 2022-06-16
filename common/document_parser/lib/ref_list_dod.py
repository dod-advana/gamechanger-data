from gamechangerml.src.section_classifier import (
    SectionClassifier,
    DocumentSections,
)
from gamechangerml.src.reference_parser.shared import is_abc_format
from gamechangerml.src.reference_parser.abc import split_refs_abc
from gamechangerml.src.reference_parser.non_abc import split_refs_non_abc


CLASSIFIER = SectionClassifier()
TOKENIZER = CLASSIFIER.tokenizer
PIPE = CLASSIFIER.pipeline


def add_ref_list_dod(doc_dict, pdf_path, tokenizer=TOKENIZER, pipe=PIPE):
    """Extract references from the DoD document and add them to doc_dict.

    Args:
        doc_dict (dict): Document and its metadata
        pdf_path (str): Path to the PDF document
        tokenizer (transformers.RobertaTokenizer)
        pipe (transformers.pipeline) Pre-trained section classifier model
    
    Returns:
        dict: The updated doc_dict, with key "ref_list" and a
            corresponding str[] value added.
    """
    sections = DocumentSections(doc_dict, tokenizer, pipe)
    references_section = sections.references_section

    if is_abc_format(references_section):
        doc_dict["ref_list"] = split_refs_abc(references_section)
    else:
        doc_dict["ref_list"] = split_refs_non_abc(
            pdf_path, references_section, tokenizer, pipe
        )

    return doc_dict
