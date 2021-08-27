#!/usr/bin/env bash
set -o errexit
set -o nounset

# main script for dev automation in gc_ingest, including crawling, parsing, and ingest
#
# main script takes 4 parameters:
#
# path-to-local-job-log-file: local path where the job log, the bash output of the script, will be placed
# base-container-name: base name for the Docker containers that will be run
# full-path-to-crawler-output-dir: local directory where the PDFs and metadata will be placed
# full-path-to-ingester-output-dir: local directory where the output of the parser and db_backup

BASE_JOB_IMAGE="10.194.9.80:5000/gamechanger/core/dev-env:latest"
HOST_REPO_DIR="$HOME/gamechanger-data"
CONTAINER_PYTHON_CMD="/opt/gc-venv/bin/python"

export DEPLOYMENT_ENV="dev"
TEST_RUN="yes"
INDEX_NAME="gamechanger_20210315"
ALIAS_NAME=""

MAX_PARSER_THREADS="12"
MAX_OCR_THREADS_PER_FILE="2"

function crawl_and_ingest() {

    [[ "$#" -ne 4 ]] && printf >&2 "Need 4 args:\n\t%s %s\n\t%s %s\n" \
            "<path-to-local-job-log-file>" \
            "<base-container-name>" \
            "<full-path-to-crawler-output-dir>" \
            "<full-path-to-ingester-output-dir>" \
        && return 1

    local local_job_log_file="${1:?Specify full path to a log file}"
    touch "$local_job_log_file"
    if [[ ! -f "$local_job_log_file" ]]; then
        >&2 printf "[ERROR] Could not create/find log file at '%s'\n" "$local_job_log_file"
    fi

    local job_timestamp="$(sed 's/.\{5\}$//' <<< $(date --iso-8601=seconds))"
    local host_repo_dir="${HOST_REPO_DIR:?Make sure to set HOST_REPO_DIR env var}"

    local base_container_name="${2:-crawl_and_ingest}"
    local crawler_host_dl_dir="${3:?How about some input?}"
    local ingest_host_raw_dir="$crawler_host_dl_dir"
    local ingest_host_job_dir="${4:?How about a job dir?}"

    local initializer_container_name="${base_container_name}_initializer"
    local crawler_container_name="${base_container_name}_crawler"
    local ingest_container_name="${base_container_name}_ingester"

    local crawler_container_image="advana/gc-downloader:latest"
    local ingest_container_image="${BASE_JOB_IMAGE:-10.194.9.80:5000/gamechanger/core/dev-env:latest}"
    local initializer_container_image="${ingest_container_image}"

    local crawler_container_dl_dir="/output"
    local ingest_container_raw_dir="/input"
    local ingest_container_job_dir="/job"

    local crawler_json_file="${ingest_container_raw_dir}/crawler_output.json"

    local es_index_name="$INDEX_NAME"
    local es_alias_name="${ALIAS_NAME:-}"

    local max_parser_threads="$MAX_PARSER_THREADS"
    local max_ocr_threads="$MAX_OCR_THREADS_PER_FILE"

    echo Cleaning up old containers...
    ( docker container rm -f "$crawler_container_name" || true ) &> /dev/null
    ( docker container rm -f "$ingest_container_name" || true ) &> /dev/null
    ( docker container rm -f "$initializer_container_name" || true) &> /dev/null

    echo Configuring repo and pulling topic models...
    ( 
      SCRIPT_ENV="$DEPLOYMENT_ENV" $HOST_REPO_DIR/paasJobs/configure_repo.sh 
    ) || echo Failed to setup repo

    echo Running Job...
    (
        # first docker run: checking the connections
        docker run \
            --name "$initializer_container_name" \
            --user "$(id -u):$(id -g)" \
            --mount type=bind,source="$host_repo_dir",destination="/gamechanger" \
            --workdir /gamechanger \
            "$ingest_container_image" bash -c \
              "$CONTAINER_PYTHON_CMD -m configuration init $DEPLOYMENT_ENV ; $CONTAINER_PYTHON_CMD -m configuration check-connections" \
        && \

        # second docker run: running the crawlers and putting them into full-path-to-crawler-output-dir
        docker run \
            --name "$crawler_container_name" \
            --user "$(id -u):$(id -g)" \
            --mount type=bind,source="$crawler_host_dl_dir",destination="$crawler_container_dl_dir" \
            --mount type=bind,source="$host_repo_dir",destination="/app" \
            --workdir "/app" \
            -e "LOCAL_DOWNLOAD_DIRECTORY_PATH=${crawler_container_dl_dir}" \
            -e "TEST_RUN=${TEST_RUN:-no}" \
            "${crawler_container_image}" \
        && \

        # third docker run: running the ingest function
        docker run \
            --name "$ingest_container_name" \
            --user "$(id -u):$(id -g)" \
            --mount type=bind,source="$host_repo_dir",destination="/gamechanger" \
            --mount type=bind,source="$ingest_host_job_dir",destination="$ingest_container_job_dir" \
            --mount type=bind,source="$crawler_host_dl_dir",destination="$ingest_container_raw_dir" \
            --workdir /gamechanger \
            "$ingest_container_image" bash -c 'source /opt/gc-venv/bin/activate; '"$CONTAINER_PYTHON_CMD"' -m dataPipelines.gc_ingest pipelines core ingest \
                --skip-snapshot-backup=yes \
                --crawler-output='"$crawler_json_file"' \
                --batch-timestamp='"$job_timestamp"' \
                --index-name='"$es_index_name"' \
                --alias-name='"$es_alias_name"' \
                --max-threads='"$max_parser_threads"' \
                --max-threads-neo4j='"$max_parser_threads"' \
                --max-ocr-threads='"$max_ocr_threads"' \
                --job-dir='"$ingest_container_job_dir"'  \
                --current-snapshot-prefix bronze/gamechanger/ \
                --backup-snapshot-prefix bronze/gamechanger/backup/ \
                --db-backup-base-prefix bronze/gamechanger/backup/db/ \
                --load-archive-base-prefix bronze/gamechanger/load-archive/ \
                --bucket-name advana-data-zone \
            local \
                --local-raw-ingest-dir '"$ingest_container_raw_dir"''

    ) 2>&1 | tee -a "$local_job_log_file"

}

crawl_and_ingest "$@"
exit $?
