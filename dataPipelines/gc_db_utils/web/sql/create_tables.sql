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
    id SERIAL NOT NULL,
    clone_name VARCHAR(512),
    display_name VARCHAR(512),
    is_live BOOLEAN NOT NULL,
    url VARCHAR(512),
    permissions_required BOOLEAN NOT NULL,
    clone_to_advana BOOLEAN NOT NULL,
    clone_to_gamechanger BOOLEAN NOT NULL,
    clone_to_sipr BOOLEAN NOT NULL,
    clone_to_jupiter BOOLEAN NOT NULL,
    show_tutorial BOOLEAN NOT NULL,
    show_graph BOOLEAN NOT NULL,
    show_crowd_source BOOLEAN NOT NULL,
    show_feedback BOOLEAN NOT NULL,
    search_module VARCHAR(512),
    export_module VARCHAR(512),
    title_bar_module VARCHAR(512),
    navigation_module VARCHAR(512),
    card_module VARCHAR(512),
    main_view_module VARCHAR(512),
    graph_module VARCHAR(512),
    search_bar_module VARCHAR(512),
    s3_bucket VARCHAR(512),
    data_source_name VARCHAR(512),
    source_agency_name VARCHAR(512),
    metadata_creation_group VARCHAR(512),
    elasticsearch_index VARCHAR(512),
    createdAt TIMESTAMP WITHOUT TIME ZONE,
    updatedAt TIMESTAMP WITHOUT TIME ZONE,
    needs_ingest BOOLEAN NOT NULL,
    source_s3_prefix VARCHAR(512),
    source_s3_bucket VARCHAR(512),

	PRIMARY KEY (id)
);

GRANT SELECT ON gc_document_corpus_snapshot to PUBLIC;
GRANT SELECT on dafa_charter_map to PUBLIC;