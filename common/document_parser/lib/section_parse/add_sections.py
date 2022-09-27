from pdf2docx import parse
from os.path import splitext, split
from os import remove

from .docx_parser import DocxParser
from .utils import Sections
from ..document import FieldNames


def add_sections(doc_dict: dict, delete_docx: bool = True) -> None:
    """Parse document sections and add them to `doc_dict`.

    Note: Only DoD document types are supported at this time. Fields will be
    empty lists for other document types.
    """
    doc_type = split(doc_dict.get(FieldNames.DOC_TYPE))[1]

    if doc_type and doc_type.lower().startswith("dod"):
        pdf_path = doc_dict.get(FieldNames.PDF_PATH)
        docx_path = splitext(pdf_path)[0] + ".docx"
        # TODO: are any of the pdfs encrypted?
        parse(pdf_path, docx_path)
        doc_num = splitext(doc_dict.get(FieldNames.DOC_NUM, ""))[0]
        pagebreak_text = " ".join([doc_type, doc_num])
        doc = DocxParser(docx_path)
        sections = doc.parse(pagebreak_text)
        if delete_docx:
            remove(docx_path)
    else:
        sections = Sections()

    doc_dict[FieldNames.SECTIONS] = {
        FieldNames.ALL_SECTIONS: sections.sections,
        FieldNames.RESPONSIBILITIES_SECTION: sections.responsibilities,
        FieldNames.REFERENCES_SECTION: sections.references,
        FieldNames.PURPOSE_SECTION: sections.purpose,
        FieldNames.SUBJECT_SECTION: sections.subject,
        FieldNames.PROCEDURES_SECTION: sections.procedures,
        FieldNames.EFFECTIVE_DATE_SECTION: sections.effective_date,
        FieldNames.APPLICABILITY_SECTION: sections.applicability,
        FieldNames.POLICY_SECTION: sections.policy,
        FieldNames.ORGANIZATIONS_SECTION: sections.organizations,
        FieldNames.DEFINITIONS_SECTION: sections.definitions,
        FieldNames.TABLE_OF_CONTENTS_SECTION: sections.table_of_contents,
        FieldNames.GLOSSARY_SECTION: sections.glossary,
        FieldNames.SUMMARY_OF_CHANGE_SECTION: sections.summary_of_change,
    }
