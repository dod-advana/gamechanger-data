# Load Tool

Tool for loading raw/processed documents into the corpus. - Including all necessary back-end storage and DB updates, but not including Neo4J & ElasticSearch updates.

## Terminology

- **Load Archive** is a timestamped storage location for all loaded documents - current and past. For example, if `<data-root>/load-archive/raw/` is the the root for timestamped directories with all raw documents, then all raw files belonging to a load that happened at `2021-01-02T12:00:00` would be stored in `<data-root>/load-archive/raw/2021-01-02T12:00:00/`
- **Raw Documents** are all documents (e.g. OCR'ed PDF files) from which text is meant to be extracted for search.
- **Metadata Documents** are any files meant to in some way enhance or complement the processing of raw documents; e.g. `doc.pdf.metadata` used to provide publication dates and other information for `doc.pdf`.
- **Processed Documents** are - typically JSON - files produced by processing raw docs and associated metadata. These processed documents are used for populating Neo4J graphs, ElasticSearch indices, and for training ML models.

## Usage

Can be used as a CLI (see cli.py) or programmatically (see utils.py). CLI usage information can be retrieved in canonical fashion by running the module and passing `--help` flag.