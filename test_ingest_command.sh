function run_core_ingest() {
  local job_dir="/home/gamechanger/de_test_scripts"
  local job_ts="2023-12-28"

  local crawler_output="$job_dir/test_ingest_crawler_output"

  local bucket_name="test_bucket"

  local es_index_name="test_index"
  local es_alias_name="current_index"

  local skip_neo4j_update="True"
  local skip_snapshot_backup="True"
  local skip_db_backup="True"
  local skip_db_update="True"
  local skip_revocation_update="True"
  local skip_thumbnail_generation="True"
  local force_ocr="True"

  local max_ocr_threads="${MAX_OCR_THREADS_PER_FILE:-4}"
  local max_parser_threads="${MAX_PARSER_THREADS:-16}"
  local max_neo4j_threads="${MAX_PARSER_THREADS:-16}"
  local max_s3_threads="${MAX_S3_THREADS:-32}"

  local current_snapshot_prefix="bronze/gamechanger/"
  local backup_snapshot_prefix="bronze/gamechanger/backup/"
  local load_archive_base_prefix="bronze/gamechanger/load-archive/"
  local db_backup_base_prefix="bronze/gamechanger/backup/db/"

  python -m dataPipelines.gc_ingest pipelines core ingest \
    --skip-neo4j-update="$skip_neo4j_update" \
    --skip-snapshot-backup="$skip_snapshot_backup" \
    --skip-db-backup="$skip_db_backup" \
    --skip-db-update="$skip_db_update" \
    --skip-thumbnail-generation="$skip_thumbnail_generation" \
    --force-ocr="$force_ocr" \
    --current-snapshot-prefix="$current_snapshot_prefix" \
    --backup-snapshot-prefix="$backup_snapshot_prefix" \
    --db-backup-base-prefix="$db_backup_base_prefix" \
    --load-archive-base-prefix="$load_archive_base_prefix" \
    --bucket-name="$bucket_name" \
    --job-dir="$job_dir" \
    --batch-timestamp="$job_ts" \
    --index-name="$es_index_name" \
    --alias-name="$es_alias_name" \
    --max-threads="$max_parser_threads" \
    --max-threads-neo4j="$max_neo4j_threads" \
    --max-ocr-threads="$max_ocr_threads" \
    --max-s3-threads="$max_s3_threads" \
    --crawler-output="$crawler_output" \
    --skip-revocation-update="$skip_revocation_update" \
    checkpoint \
    --checkpoint-limit=1 \
    --checkpoint-file-path="bronze/gamechanger/external-uploads/crawler-downloader/checkpoint.txt" \
    --checkpointed-dir-path="bronze/gamechanger/external-uploads/crawler-downloader/" \
    --checkpoint-ready-marker="manifest.json" \
    --advance-checkpoint="yes"

}

run_core_ingest
