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

CREATE TABLE IF NOT EXISTS clone_meta (
	id = INTEGER,
    clone_name VARCHAR(512) NOT NULL,
    display_name VARCHAR(512) NOT NULL,
    is_live BOOLEAN NOT NULL,
    url VARCHAR(512) NOT NULL,
    permissions_required BOOLEAN NOT NULL,
    clone_to_advana BOOLEAN NOT NULL,
    clone_to_gamechanger BOOLEAN NOT NULL,
    clone_to_sipr BOOLEAN NOT NULL,
    clone_to_jupiter BOOLEAN NOT NULL,
    show_tutorial BOOLEAN NOT NULL,
    show_graph BOOLEAN NOT NULL,
    show_crowd_source BOOLEAN NOT NULL,
    show_feedback BOOLEAN NOT NULL,
    search_module VARCHAR(512) NOT NULL,
    export_module VARCHAR(512) NOT NULL,
    title_bar_module VARCHAR(512) NOT NULL,
    navigation_module VARCHAR(512) NOT NULL,
    card_module VARCHAR(512) NOT NULL,
    main_view_module VARCHAR(512) NOT NULL,
    graph_module VARCHAR(512) NOT NULL,
    search_bar_module VARCHAR(512) NOT NULL,
    s3_bucket VARCHAR(512) NOT NULL,
    metadata_creation_group VARCHAR(512) NOT NULL,
    elasticsearch_index VARCHAR(512) NOT NULL,
    createdAt TIMESTAMP WITHOUT TIME ZONE,
    updatedAt TIMESTAMP WITHOUT TIME ZONE,
    needs_ingest BOOLEAN NOT NULL,
    source_s3_prefix VARCHAR(512) NOT NULL,
    source_s3_bucket VARCHAR(512) NOT NULL,
    PRIMARY KEY (id)
);

GRANT SELECT ON gc_document_corpus_snapshot to PUBLIC;
GRANT SELECT on dafa_charter_map to PUBLIC;