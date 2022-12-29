class FieldNames:
    """Field names for dictionary representations of documents."""

    FILENAME = "filename"
    PAGES = "pages"
    PAGE_RAW_TEXT = "p_raw_text"

    PARAGRAPHS = "paragraphs"
    PAGE_NUM = "page_num_i"
    PAR_COUNT = "par_count_i"  # Paragraph index within the given page
    PAR_INC_COUNT = (
        "par_inc_count"  # Paragraph index within the entire document
    )
    PAR_RAW_TEXT = "par_raw_text_t"

    ID = "id"
    TYPE = "type"

    ENTITIES = "entities"
    TOP_ENTITIES = "top_entities_t"

