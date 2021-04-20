# Snapshot Tool

Tool for update, backup, & restore ops on snapshots.

## Terminology

Snapshot is a state of document corpus at a given point in time and consist of all raw and processed documents, but does not include the state of ES indexes or Neo4J graphs

For example, a "current snapshot", is the set of all raw and processed documents currently accessible by the application. This snapshot is typically materialized and lives at `<data-root>/pdf/` for raw documents and `<data-root>/json/` for processed documents.

## Usage

Can be used as a CLI (see cli.py) or programmatically (see utils.py). CLI usage information can be retrieved in canonical fashion by running the module and passing `--help` flag.