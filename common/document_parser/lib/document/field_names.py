class FieldNames:
    """Field names for dictionary representations of documents."""

    FILENAME = "filename"
    TITLE = "title"
    DOC_TYPE = "doc_type"
    DOC_NUM = "doc_num"
    ID = "id"
    TYPE = "type"

    TEXT = "text"  # Text of the entire document.

    PAGES = "pages"
    PAGE_RAW_TEXT = "p_raw_text"  # Raw text of a page.

    PARAGRAPHS = "paragraphs"
    PAGE_NUM = "page_num_i"
    PAR_COUNT = "par_count_i"  # Paragraph index within the given page
    PAR_INC_COUNT = (
        "par_inc_count"  # Paragraph index within the entire document
    )
    PAR_RAW_TEXT = "par_raw_text_t"  # Raw text of a paragraph.

    ENTITIES = "entities"
    TOP_ENTITIES = "top_entities_t"

    SECTIONS = "sections"
    ALL_SECTIONS = "all_sections"
    RESPONSIBILITIES_SECTION = "responsibilities_section"
    REFERENCES_SECTION = "references_section"
    PURPOSE_SECTION = "purpose_section"
    SUBJECT_SECTION = "subject_section"
    PROCEDURES_SECTION = "procedures_section"
    EFFECTIVE_DATE_SECTION = "effective_date_section"
    APPLICABILITY_SECTION = "applicability_section"
    POLICY_SECTION = "policy_section"
    ORGANIZATIONS_SECTION = "organizations_section"
    DEFINITIONS_SECTION = "definitions_section"
    TABLE_OF_CONTENTS_SECTION = "table_of_contents"
    GLOSSARY_SECTION = "glossary_section"
    SUMMARY_OF_CHANGE_SECTION = "summary_of_change_section"
