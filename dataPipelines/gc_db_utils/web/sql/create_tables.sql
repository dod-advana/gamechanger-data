CREATE TABLE IF NOT EXISTS gc_document_corpus_snapshot (
	doc_id INTEGER NOT NULL,
	pub_id INTEGER NOT NULL,
	pub_name VARCHAR(512) NOT NULL,
	pub_title VARCHAR(512) NOT NULL,
	pub_type VARCHAR(512) NOT NULL,
	pub_number VARCHAR(512) NOT NULL,
	pub_is_revoked BOOLEAN NOT NULL,
	doc_filename VARCHAR(512),
	doc_s3_location VARCHAR(512),
	upload_date TIMESTAMP WITHOUT TIME ZONE,
	publication_date TIMESTAMP WITHOUT TIME ZONE,
	json_metadata JSON,

	PRIMARY KEY (doc_id)
);

CREATE TABLE IF NOT EXISTS dafa_charter_map (
	org_abbreviation VARCHAR(512) NOT NULL,
	org_name VARCHAR(512) NOT NULL,
	pub_id INTEGER,
	PRIMARY KEY (org_abbreviation, org_name),
	UNIQUE (pub_id)
);

GRANT SELECT ON gc_document_corpus_snapshot to PUBLIC;
GRANT SELECT on dafa_charter_map to PUBLIC;