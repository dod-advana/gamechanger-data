from pdf2docx import parse
from os.path import splitext, split
from os import remove
from typing import Callable

from common.document_parser.cli import get_default_logger
from .docx_parser import DocxParser
from .utils import Sections
from ..document import FieldNames


LOGGER = get_default_logger()


def add_sections(doc_dict: dict, delete_docx: bool = True) -> None:
    """Parse document sections and add them to `doc_dict`.

    Note: Only DoD document types are supported at this time. Fields will be
    empty lists for other document types.
    """
    doc_type = split(doc_dict.get(FieldNames.DOC_TYPE))[1]

    sections = None
    if doc_type and doc_type.lower().startswith("dod"):
        pdf_path = doc_dict.get(FieldNames.PDF_PATH)
        docx_path = splitext(pdf_path)[0] + ".docx"
        success_3 = False
        fail_msg = "Cannot parse sections."

        # TODO: are any of the pdfs encrypted?
        _, success_1 = _attempt(
            parse,
            (pdf_path, docx_path),
            f"Failed to convert to docx: `{docx_path}`. {fail_msg}",
        )

        if success_1:
            doc, success_2 = _attempt(
                DocxParser,
                (docx_path,),
                f"Failed to init DocxParser for `{docx_path}`. {fail_msg}",
            )
            if success_2:
                doc_num = splitext(doc_dict.get(FieldNames.DOC_NUM, ""))[0]
                pagebreak_text = " ".join([doc_type, doc_num])
                sections, success_3 = _attempt(
                    doc.parse,
                    (pagebreak_text,),
                    f"Failed to parse sections of `{docx_path}`. {fail_msg}",
                )

        if success_3 and delete_docx:
            remove(docx_path)

    if sections is None:
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

def _attempt(func: Callable, args, fail_msg: str) -> bool:
    try:
        val = func(*args)
    except:
        LOGGER.exception(fail_msg)
        return None, False

    return val, True
