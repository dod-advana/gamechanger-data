# Gamechanger Data Pipelines

Here live the gamechanger data pipelines.

## How packages are used/organized

All packages under `dataPipelines` typically have some sort of CLI that can be invoked by running said package as a module, for example `python -m dataPipelines.gc_downloader --help`

All of the heavy lifting for given part of the data pipeline is performed in one python package or another; however, in order to run complete data pipelines in various environments, they are typically wrapped in some shell script. - The shell scripts (and corresponding pipeline definitions) used to run data pipelines in StreamSets are maintained in the `<repo>/dataPipelines/streamsets_pipelines/` hierarchy. 

Almost all tools here connect to various backends by using helper methods/classes provided in the `<repo>/configuration/` package. - See the `README.md` therein for more info.

The `<repo>/dataPipelines/gc_ingest/` CLI is the complete solution for running all steps of the ingest. However, some of the more special use cases may not be implemented there yet. - See the README files within that package hierarchy for more info (esp one in `gc_ingest/pipelines/core/`).

## Configuration

All backend configuration/endpoints/credentials is handled in the `<repo>/configuration/`. See README therein for more info. As long as correct configuration JSON files are placed into the `<repo>/configuration/app-config/` and `<repo>/configuration/elasticsearch-config/`, setting the configuration is as simple as running `python -m configuration init <config-filename-without-json-suffix>`. - For example, local development: `python -m configuration init local`

## Getting Started Guide

Data ingest can be thought of as an ordered set of activities:

- Getting raw publication data
- Turning raw publication data into processed JSON format
- Using processed JSON documents for
    - Updating ElasticSearch Index
    - Updating Neo4J Graph
    - Training ML Models

### Getting raw publication data

Data comes from many sources and the question is largely of whether the data in question is of the format (or can be coerced to a format) that is supported by the existing tools. `<repo>/common/document_parser/` package provides CLI for processing raw publication data and determines what formats are or aren't supported. Input format du jour is PDF and `document_parser` can perform OCR on it if it's not already OCR'ed. 

The many sub packages in `<repo>/dataPipelines/gc_crawler/` are used to obtain raw data from web crawlers. - The process is broken up into figuring out which files to download (that's stuff in `gc_crawler`) and actually downloading them (using `/repo/dataPipelines/gc_downloader/`)  

### Turning raw publication data into processed JSON format

The `<repo>/common/document_parser/` CLI tool is used to turn raw documents into processed JSON's. See README.md therein for more info.

### Updating ElasticSearch Index

With processed JSON's in hand. You can use `<repo>/dataPipelines/gc_elasticsearch_publisher/` CLI tool in order to create or update an ElasticSearch index. Configuration of ElasticSearch connection, settings, and mappings is handled in the `<repo>/configuration/` package (see relevant README therein).

### Updating Neo4j Graph
With processed JSON's in hand, You can use `<repo>/dataPipelines/gc_neo4j_publisher/` CLI tool in order to create/update Neo4j graph.

### Training ML Models
If it becomes necessary to train ML model on a new data, there would typically be a relevant script inside of [gamechanger-ml](https://github.com/dod-advana/gamechanger-ml) repo hierarchy to fill the need. Exactly which script that might be or how that works is in costant flux, so consult relevant docs in that part of the repo to find out.

### Nuances

Although the high level parts of the data ingest are straightforward, the things get considerably more complicated when considering requirements of data ingest like maintaining historical versions of documents and enabling updates of existing corpus without duplication. Such nuances are handled through additional load orchestration logic and are described in more detail in the `dataPipelines/gc_ingest/tools/load/README.md`.
