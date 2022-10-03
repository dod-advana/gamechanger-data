class FieldNames:
    """Field names for dictionary representations of documents."""

    FILENAME = "filename"
    TEXT = "text"
    PAGES = "pages"
    PAGE_RAW_TEXT = "p_raw_text"

    PARAGRAPHS = "paragraphs"
    PAGE_NUM = "page_num"
    PAR_COUNT = "par_count_i"  # Paragraph index within the given page
    PAR_INC_COUNT = (
        "par_inc_count"  # Paragraph index within the entire document
    )
    PAR_RAW_TEXT = "par_raw_text_t"

    ID = "id"
    TYPE = "type"

    ENTITIES = "entities"
    TOP_ENTITIES = "top_entities_t"

    DOC_TYPE = "doc_type"
    DOC_NUM = "doc_num"

    # Full path to the pdf file. 
    # Note: This field is deleted during the post process step 
    # (common/document_parser_parsers/policy_analytics/parse.py).
    PDF_PATH = "pdf_path"  

    SECTIONS = "sections"
    ALL_SECTIONS = "all_sections"
    RESPONSIBILITIES_SECTION = "responsibilities_section"
    REFERENCES_SECTION = "references_section"
    PURPOSE_SECTION = "purpose_section"
    SUBJECT_SECTION = "subject_section"
    PROCEDURES_SECTION = "procedures_section"
    EFFECTIVE_DATE_SECTION = "effective_date"
    APPLICABILITY_SECTION = "applicability_section"
    POLICY_SECTION = "policy_section"
    ORGANIZATIONS_SECTION = "organizations_section"
    DEFINITIONS_SECTION = "definitions_section"
    TABLE_OF_CONTENTS_SECTION = "table_of_contents"
    GLOSSARY_SECTION = "glossary_section"
    SUMMARY_OF_CHANGE_SECTION = "summary_of_change_section"
