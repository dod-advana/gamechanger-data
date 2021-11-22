#!/usr/bin/env bash
set -o nounset
set -o errexit
set -o pipefail

function main() {
  local job_ts=$(date +%FT%T)
  local job_ts_simple=$(date --date="$job_ts" +%Y%m%d_%H%M%S)
  
  local max_cpu_count
  case "${OSTYPE:-linux}" in
    "*darwin*") max_cpu_count=$(sysctl -n hw.ncpu) ;;
    *) max_cpu_count=$(grep -c ^processor /proc/cpuinfo) ;;
  esac
  
  local default_cpu_count=$max_cpu_count
  local default_thread_count=$((default_cpu_count * 2))
  local default_ocr_thread_count=$((default_cpu_count / 2))

  local raw_doc_dir=${1:?"Must specify raw doc dir: arg #1"}
  local parsed_doc_dir=${2:-}

  local batch_timestamp=${job_ts}

  local current_snapshot_prefix="bronze/gamechanger/"
  local backup_snapshot_prefix="bronze/gamechanger/backup/"
  local load_archive_base_prefix="bronze/gamechanger/load-archive/"
  local db_backup_base_prefix="bronze/gamechanger/backup/db/"
  
  local bucket_name=${S3_BUCKET_NAME}
  local es_index_name=${ES_INDEX_NAME:-gamechanger_${job_ts_simple}}
  local es_alias_name=${ES_ALIAS_NAME:-gamechanger}
  local job_dir=${LOCAL_TMP_DIR:-$(mktemp -d)}

  local max_ocr_threads=${MAX_OCR_THREADS_PER_FILE:-${default_ocr_thread_count}}
  local max_parser_threads=${MAX_PARSER_THREADS:-${default_cpu_count}}
  local max_neo4j_threads=${MAX_PARSER_THREADS:-${default_cpu_count}}
  local max_s3_threads=${MAX_S3_THREADS:-${default_thread_count}}

  local skip_neo4j_update=${SKIP_NEO4J_UPDATE:-no}
  local skip_snapshot_backup=${SKIP_SNAPSHOT_BACKUP:-no}
  local skip_db_backup=${SKIP_DB_BACKUP:-no}
  local skip_db_update=${SKIP_DB_UPDATE:-no}

  local local_raw_ingest_dir=/tmp/raw
  local local_parsed_ingest_dir=/tmp/parsed

  python -m dataPipelines.gc_ingest pipelines core ingest \
    --skip-neo4j-update="$skip_neo4j_update" \
    --skip-snapshot-backup="$skip_snapshot_backup" \
    --skip-db-backup="$skip_db_backup" \
    --skip-db-update="$skip_db_update" \
    --current-snapshot-prefix="$current_snapshot_prefix" \
    --backup-snapshot-prefix="$backup_snapshot_prefix" \
    --db-backup-base-prefix="$db_backup_base_prefix" \
    --load-archive-base-prefix="$load_archive_base_prefix" \
    --bucket-name="$bucket_name" \
    --job-dir="$job_dir" \
    --batch-timestamp="$batch_timestamp" \
    --index-name="$es_index_name" \
    --alias-name="$es_alias_name" \
    --max-threads="$max_parser_threads" \
    --max-threads-neo4j="$max_neo4j_threads" \
    --max-ocr-threads="$max_ocr_threads" \
    --max-s3-threads="$max_s3_threads" \
    local \
    --local-raw-ingest-dir="$raw_doc_dir" \
    ${parsed_doc_dir:+"--local-parsed-ingest-dir=$parsed_doc_dir"}
}

main "$@"