CREATE TEMPORARY TABLE manual_mappings (
    org_abbreviation VARCHAR,
    org_name VARCHAR,
    pub_type VARCHAR,
    pub_number VARCHAR
) ON COMMIT PRESERVE ROWS ;

INSERT INTO manual_mappings VALUES
('DARPA','Defense Advanced Research Projects Agency','DoDD','5134.10'),
('DCAA','Defense Contract Audit Agency','DoDD','5105.36'),
('DCMA','Defense Contract Management Agency','DoDD','5105.64'),
('DeCA','Defense Commissary Agency','DoDD','5105.55'),
('DFAS','Defense Finance and Accounting Service','DoDD','5118.05'),
('DHA','Defense Health Affairs','DoDD','5136.13'),
('DHRA','Defense Human Resource Activities','DoDD','5100.87'),
('DIA','Defense Intelligence Agency','DoDD','5105.21'),
('DISA','Defense Information Systems Agency','DoDD','5105.19'),
('DLA','Defense Logistics Agency','DoDD','5105.22'),
('DLSA','Defense Legal Services Agency','DoDD','5145.04'),
('DMA','Defense Media Activity','DoDD','5105.74'),
('DoDEA','Department of Defense Education Activity','DoDD','1342.20'),
('DPAA','Defense POW/MIA Accounting Agency','DoDD','5110.10'),
('DSCA','Defense Security Cooperation Agency','DoDD','5105.65'),
('DSS','Defense Security Service','DoDD','5105.42'),
('DTIC','Defense Technical Informatino Center','DoDD','5105.73'),
('DTRA','Defense Threat Reduction Agency','DoDD','5105.62'),
('DTRMC','DoD Test Resource Management Center','DoDD','5105.71'),
('DTSA','Defense Technology Security Agency','DoDD','5105.72'),
('MDA','Missile Defense Agency','DoDD','5134.09'),
('NGA','National Geospatial-Intelligence Agency','DoDD','5105.60'),
('NRO','National Reconnaissance Office','DoDD','5105.23'),
('NSA/CSS','National Security Agency','DoDD','5100.20'),
('OEA','Office of Economic Adjustment','DoDD','3030.01'),
('PFPA','Pentagon Force Protection Agency','DoDD','5105.68'),
('WHS','Washington Headquarters Services','DoDD','5110.04')
;

DELETE FROM dafa_charter_map;
INSERT INTO dafa_charter_map
SELECT
    org_abbreviation,
    org_name,
    s.pub_id
FROM
    manual_mappings m LEFT OUTER JOIN gc_document_corpus_snapshot s ON
    m.pub_type = s.pub_type AND m.pub_number = s.pub_number
;

COMMIT;

GRANT SELECT ON dafa_charter_map to PUBLIC;
GRANT SELECT ON dafa_charter_map_flattened_vw to PUBLIC;