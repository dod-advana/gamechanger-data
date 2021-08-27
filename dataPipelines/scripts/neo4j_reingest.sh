set -o errexit
set -o nounset

# script to run the update-neo4j function in gc_ingest
#
# update-neo4j script takes 3 parameters:
#
# path-to-local-job-log-file: local path where the job log, the bash output of the script, will be placed
# base-container-name: base name for the Docker containers that will be run
# full-path-to-ingester-output-dir: local directory where the jsons/output of the parser will be pulled for updating neo4j

BASE_JOB_IMAGE="10.194.9.80:5000/gamechanger/core/dev-env:latest"
HOST_REPO_DIR="$HOME/gamechanger-data"
CONTAINER_PYTHON_CMD="/opt/gc-venv/bin/python"

DEPLOYMENT_ENV="dev"

INDEX_NAME="gamechanger_20210315"
ALIAS_NAME=""

MAX_PARSER_THREADS="12"
MAX_OCR_THREADS_PER_FILE="2"

function update_neo4j() {

    [[ "$#" -ne 3 ]] && printf >&2 "Need 3 args:\n\t%s %s\n\t%s %s\n" \
            "<path-to-local-job-log-file>" \
            "<base-container-name>" \
            "<full-path-to-ingester-output-dir>" \
        && return 1

    local local_job_log_file="${1:?Specify full path to a log file}"
    touch "$local_job_log_file"
    if [[ ! -f "$local_job_log_file" ]]; then
        >&2 printf "[ERROR] Could not create/find log file at '%s'\n" "$local_job_log_file"
    fi

    local job_timestamp="$(sed 's/.\{5\}$//' <<< $(date --iso-8601=seconds))"
    local host_repo_dir="${HOST_REPO_DIR:?Make sure to set HOST_REPO_DIR env var}"

    local base_container_name="${2:-neo4j}"
    local ingest_host_job_dir="${3:?How about a job dir?}"

    local ingest_container_name="${base_container_name}_neo4j_ingester"

    local ingest_container_image="${BASE_JOB_IMAGE:-10.194.9.80:5000/gamechanger/core/dev-env:latest}"

    local crawler_container_dl_dir="/output"
    local ingest_container_raw_dir="/input"
    local ingest_container_job_dir="/job"

    local es_index_name="$INDEX_NAME"
    local es_alias_name="${ALIAS_NAME:-}"

    local max_parser_threads="$MAX_PARSER_THREADS"
    local max_ocr_threads="$MAX_OCR_THREADS_PER_FILE"

    echo Cleaning up old containers...
    ( docker container rm -f "$ingest_container_name" || true ) &> /dev/null

    echo Running Job...
    (
        docker run \
            --name "$ingest_container_name" \
            --user "$(id -u):$(id -g)" \
            --mount type=bind,source="$host_repo_dir",destination="/gamechanger" \
            --mount type=bind,source="$ingest_host_job_dir",destination="$ingest_container_job_dir" \
            --workdir /gamechanger \
            "$ingest_container_image" "$CONTAINER_PYTHON_CMD" -m dataPipelines.gc_ingest pipelines core ingest \
                --skip-snapshot-backup=yes \
                --batch-timestamp="$job_timestamp" \
                --index-name="$es_index_name" \
                --alias-name="$es_alias_name" \
                --max-threads="$max_parser_threads" \
                --max-threads-neo4j="$max_parser_threads" \
                --max-ocr-threads="$max_ocr_threads" \
                --job-dir="$ingest_container_job_dir"  \
                --current-snapshot-prefix bronze/gamechanger/ \
                --backup-snapshot-prefix bronze/gamechanger/backup/ \
                --db-backup-base-prefix bronze/gamechanger/backup/db/ \
                --load-archive-base-prefix bronze/gamechanger/load-archive/ \
                --bucket-name advana-data-zone \
            update-neo4j
    ) 2>&1 | tee -a "$local_job_log_file"

}


update_neo4j "$@"
exit $?
