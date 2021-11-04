CREATE TABLE IF NOT EXISTS publications (
	id SERIAL NOT NULL,
	name VARCHAR(512) NOT NULL,
	title VARCHAR(512) NOT NULL,
	type VARCHAR(512) NOT NULL,
	number VARCHAR(512),
	is_ignored BOOLEAN NOT NULL,
	is_revoked BOOLEAN NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (name)
);

CREATE TABLE IF NOT EXISTS versioned_docs (
	id SERIAL NOT NULL,
	pub_id INTEGER NOT NULL,
	name VARCHAR(512) NOT NULL,
	type VARCHAR(512) NOT NULL,
	number VARCHAR(512) NOT NULL,
	filename VARCHAR(512) NOT NULL,
	doc_location VARCHAR(512),
	batch_timestamp TIMESTAMP WITHOUT TIME ZONE NOT NULL,
	publication_date TIMESTAMP WITHOUT TIME ZONE,
	json_metadata JSON,
	version_hash VARCHAR(512),
	md5_hash VARCHAR(512),
	is_ignored BOOLEAN NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(pub_id) REFERENCES publications (id)
);

CREATE TABLE IF NOT EXISTS pipeline_jobs (
	id SERIAL NOT NULL,
	name VARCHAR(512),
	started_ts TIMESTAMP WITHOUT TIME ZONE NOT NULL,
	finished_ts TIMESTAMP WITHOUT TIME ZONE,
	sigkill_sent_ts TIMESTAMP WITHOUT TIME ZONE,
	pid INTEGER NOT NULL,
	PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS crawler_status (
	id SERIAL NOT NULL,
	crawler_name VARCHAR(512) NOT NULL,
	status VARCHAR(512) NOT NULL,
	datetime TIMESTAMP NOT NULL,
	PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS crawler_info (
    id SERIAL NOT NULL,
    crawler character varying(512) NOT NULL,
    display_source_s character varying(512) NOT NULL,
    source_title character varying(512) NOT NULL,
    display_org character varying(512) NOT NULL,
    url_origin character varying(512),
    image_link character varying(512),
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS organization_info (
    id SERIAL NOT NULL,
    display_org character varying(512) NOT NULL,
    image_link character varying(512),
    PRIMARY KEY (id)
);



GRANT SELECT ON crawler_status TO PUBLIC;
