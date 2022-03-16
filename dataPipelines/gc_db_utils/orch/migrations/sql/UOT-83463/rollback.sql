DROP VIEW gc_document_corpus_snapshot_vw ;
CREATE OR REPLACE VIEW gc_document_corpus_snapshot_vw AS
SELECT
       v.id as doc_id,
       p.id as pub_id,
       p.name as pub_name,
       p.title as pub_title,
       p.type as pub_type,
       p.number as pub_number,
       v.filename as doc_filename,
       v.doc_location as doc_s3_location,
       v.batch_timestamp as upload_date,
       v.publication_date as publication_date,
       v.json_metadata as json_metadata
FROM
    publications p
    JOIN
    (
        SELECT vd.*
        FROM
            versioned_docs vd
            JOIN
            (
                SELECT DISTINCT pub_id, batch_timestamp
                FROM (
                         SELECT pub_id,
                                MAX(versioned_docs.batch_timestamp)
                                    OVER (PARTITION BY pub_id)
                                AS batch_timestamp
                         FROM versioned_docs
                     ) vd_snapshot_map_agg
            ) vd_snapshot_map
            ON
                vd.pub_id = vd_snapshot_map.pub_id
                    AND
                vd.batch_timestamp =  vd_snapshot_map.batch_timestamp
    ) v
    ON
        p.id = v.pub_id
WHERE
      NOT (p.is_revoked OR p.is_ignored)
        AND
      NOT (v.is_ignored)