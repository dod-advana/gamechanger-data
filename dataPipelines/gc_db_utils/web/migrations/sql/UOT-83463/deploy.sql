ALTER TABLE IF EXISTS gc_document_corpus_snapshot ADD pub_is_revoked BOOLEAN DEFAULT FALSE NOT NULL ;
UPDATE gc_document_corpus_snapshot SET pub_is_revoked = FALSE;
ALTER TABLE gc_document_corpus_snapshot ALTER COLUMN pub_is_revoked DROP DEFAULT;
COMMIT;
