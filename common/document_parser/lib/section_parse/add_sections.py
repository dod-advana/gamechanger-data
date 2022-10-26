from .parsers import ParserFactory
from common.document_parser.lib.document import FieldNames


def add_sections(doc_dict: dict) -> None:
    """Parse document sections and add them to `doc_dict`.

    Note: Only some document types are supported at this time. Fields will be
    empty lists for unsupported document types.
    """
    parser = ParserFactory.create(doc_dict)
    doc_dict[FieldNames.SECTIONS] = {
        FieldNames.ALL_SECTIONS: parser.all_sections,
        FieldNames.RESPONSIBILITIES_SECTION: parser.responsibilities,
        FieldNames.REFERENCES_SECTION: parser.references,
        FieldNames.PURPOSE_SECTION: parser.purpose,
        FieldNames.SUBJECT_SECTION: parser.subject,
        FieldNames.PROCEDURES_SECTION: parser.procedures,
        FieldNames.EFFECTIVE_DATE_SECTION: parser.effective_date,
        FieldNames.APPLICABILITY_SECTION: parser.applicability,
        FieldNames.POLICY_SECTION: parser.policy,
        FieldNames.ORGANIZATIONS_SECTION: parser.organizations,
        FieldNames.DEFINITIONS_SECTION: parser.definitions,
        FieldNames.TABLE_OF_CONTENTS_SECTION: parser.table_of_contents,
        FieldNames.GLOSSARY_SECTION: parser.glossary,
        FieldNames.SUMMARY_OF_CHANGE_SECTION: parser.summary_of_change,
    }
