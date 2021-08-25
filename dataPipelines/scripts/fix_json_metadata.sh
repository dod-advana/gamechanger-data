#!/usr/bin/env bash
set -o errexit
set -o nounset

# this function changes the json_metadata field of the Versioned_docs table from a string to JSON type
# (does nothing if JSON)
python -m dataPipelines.gc_ingest tools load \
  --bucket-name "advana-data-zone" \
  --load-archive-base-prefix "bronze/gamechanger/load-archive/" \
  fix-json-metadata

# this function refreshes the view that produces the gc_document_corpus_snapshot

python -m dataPipelines.gc_ingest tools db \
  --db-backup-base-prefix "bronze/gamechanger/backup/db/" \
  --bucket-name "advana-data-zone" \
  refresh \
  --db "web"
