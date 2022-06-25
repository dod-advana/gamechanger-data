# Example Runs

```bash
# dont update neo4j and run crawler and parser
./scripts/steps.sh -j dod-test-strategy -c dod_strategy_spider
# update neo4j and run crawler and dont parser
./scripts/steps.sh -j dod-test-strategy -c dod_strategy_spider -u yes
```

## Test Harness

```bash
python -m dev_tools.universal_test_harness setup
python -m dev_tools.universal_test_harness neo peek
python -m dev_tools.universal_test_harness neo purge
```

### Parse Docs

```bash
python -m common.document_parser pdf-to-json \
    -w -s tmp/test-runs/dod-policy/crawler-output \
    -d tmp/test-runs/dod-policy/parsed_docs
```

### Update Neo4J
```bash
python -m dataPipelines.gc_ingest pipelines core ingest \
    --skip-neo4j-update=no \
    --skip-snapshot-backup=yes \
    --skip-db-backup=no \
    --skip-db-update=no \
    --current-snapshot-prefix="gamechanger/test-output-steps/" \
    --backup-snapshot-prefix="gamechanger/test-output-steps/backup" \
    --db-backup-base-prefix="gamechanger/test-output-steps/backup/db/" \
    --load-archive-base-prefix="gamechanger/test-output-steps/load-archive" \
    --bucket-name="advana-data-zone" \
    --job-dir="tmp/test-runs/test-dod-spider" \
    --batch-timestamp="2022-06-21T01:19:31" \
    --index-name="gamechanger_20210409" \
    --alias-name=\'\' \
    --max-threads=16 \
    --max-ocr-threads=4 \
    --max-s3-threads=1 \
    --skip-revocation-update=no \
    --skip-es-revocation=yes \
    update-neo4j
```