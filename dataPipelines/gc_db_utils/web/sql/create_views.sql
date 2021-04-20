CREATE OR REPLACE VIEW dafa_charter_map_flattened_vw AS
SELECT
    org_abbreviation,
    org_name,
    t1.pub_id,
    pub_name,
    pub_type,
    pub_number,
    pub_title,
    publication_date,
    doc_filename
FROM dafa_charter_map t1 LEFT OUTER JOIN gc_document_corpus_snapshot t2
    ON
        t1.pub_id = t2.pub_id
;

GRANT SELECT ON dafa_charter_map_flattened_vw TO PUBLIC;