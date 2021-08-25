#!/usr/bin/env bash
set -o errexit
set -o nounset

REVERT="${REVERT-no}"

# this function changes the json_metadata field of the Versioned_docs table from a string to JSON type
# (does nothing if JSON)

if [[ "$REVERT" = "no" ]] ; then
   echo "JSON_METADATA TO JSON"
   python -m dataPipelines.gc_ingest tools load \
     --bucket-name "advana_raw_zone" \
     --load-archive-base-prefix "gamechanger/load-archive/" \
     json-metadata-to-json
fi

if [[ "$REVERT" = "yes" ]] ; then
   echo "JSON_METADATA TO STRING"
   python -m dataPipelines.gc_ingest tools load \
     --bucket-name "advana_raw_zone" \
     --load-archive-base-prefix "gamechanger/load-archive/" \
     json-metadata-to-string
fi
# this function refreshes the view that produces the gc_document_corpus_snapshot

python -m dataPipelines.gc_ingest tools db \
  --db-backup-base-prefix "bronze/gamechanger/backup/db/" \
  --bucket-name "advana-data-zone" \
  refresh \
  --db "web"
