
CREATE TABLE IF NOT EXISTS crawler_status (
	id SERIAL NOT NULL,
	crawler_name VARCHAR(512) NOT NULL,
	status VARCHAR(512) NOT NULL,
	datetime TIMESTAMP NOT NULL,
	PRIMARY KEY (id)
);
GRANT SELECT ON crawler_status TO PUBLIC;
INSERT INTO crawler_status(id, crawler_name,status, datetime)
VALUES (DEFAULT, 'army_pubs', 'Ingest Complete', '2021-02-18T22:52:03');
INSERT INTO crawler_status(id, crawler_name,status, datetime)
VALUES (DEFAULT, 'dod_issuances', 'Ingest Complete', '2021-02-18T22:52:03');
INSERT INTO crawler_status(id, crawler_name,status, datetime)
VALUES (DEFAULT, 'ic_policies', 'Ingest Complete', '2021-02-18T22:52:03');
INSERT INTO crawler_status(id, crawler_name,status, datetime)
VALUES (DEFAULT, 'us_code', 'Ingest Complete', '2021-02-18T22:52:03');
INSERT INTO crawler_status(id, crawler_name,status, datetime)
VALUES (DEFAULT, 'ex_orders', 'Ingest Complete', '2021-02-18T22:52:03');
INSERT INTO crawler_status(id, crawler_name,status, datetime)
VALUES (DEFAULT, 'opm_pubs', 'Ingest Complete', '2021-02-18T22:52:03');
INSERT INTO crawler_status(id, crawler_name,status, datetime)
VALUES (DEFAULT, 'air_force_pubs', 'Ingest Complete', '2021-02-18T22:52:03');
INSERT INTO crawler_status(id, crawler_name,status, datetime)
VALUES (DEFAULT, 'marine_pubs', 'Ingest Complete', '2021-02-18T22:52:03');
INSERT INTO crawler_status(id, crawler_name,status, datetime)
VALUES (DEFAULT, 'secnav_pubs', 'Ingest Complete', '2021-02-18T22:52:03');
INSERT INTO crawler_status(id, crawler_name,status, datetime)
VALUES (DEFAULT, 'navy_med_pubs', 'Ingest Complete', '2021-02-18T22:52:03');
INSERT INTO crawler_status(id, crawler_name,status, datetime)
VALUES (DEFAULT, 'navy_reserves', 'Ingest Complete', '2021-02-18T22:52:03');
INSERT INTO crawler_status(id, crawler_name,status, datetime)
VALUES (DEFAULT, 'Bupers_Crawler', 'Ingest Complete', '2021-02-18T22:52:03');
INSERT INTO crawler_status(id, crawler_name,status, datetime)
VALUES (DEFAULT, 'milpersman_crawler', 'Ingest Complete', '2021-02-18T22:52:03');
INSERT INTO crawler_status(id, crawler_name,status, datetime)
VALUES (DEFAULT, 'nato_stanag', 'Ingest Complete', '2021-02-18T22:52:03');
INSERT INTO crawler_status(id, crawler_name,status, datetime)
VALUES (DEFAULT, 'fmr_pubs', 'Ingest Complete', '2021-02-18T22:52:03');

COMMIT;