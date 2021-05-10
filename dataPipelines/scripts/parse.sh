set -o errexit
set -o nounset

# script to just run the parse function on a directory of pdf/metadata without ingest
#
# parse script takes 4 parameters:
#
# path-to-local-job-log-file: local path where the job log, the bash output of the script, will be placed
# base-container-name: base name for the Docker containers that will be run
# full-path-to-crawler-output-dir: local directory where the PDFs and metadata are
# full-path-to-ingester-output-dir: local directory where the jsons/output of the parser will go

BASE_JOB_IMAGE="10.194.9.80:5000/gamechanger/core/dev-env:latest"
HOST_REPO_DIR="$HOME/gamechanger"
CONTAINER_PYTHON_CMD="/opt/gc-venv/bin/python"

function parse() {

    [[ "$#" -ne 4 ]] && printf >&2 "Need 4 args:\n\t%s %s\n\t%s %s\n" \
        "<base-container-name>" \
        "<path-to-pdf-files>" \
        "<path-to-json-output>" \
        "<path-to-job-file>" \
    && return 1

    local local_job_log_file="${1:?Specify full path to a log file}"
    touch "$local_job_log_file"
    if [[ ! -f "$local_job_log_file" ]]; then
        >&2 printf "[ERROR] Could not create/find log file at '%s'\n" "$local_job_log_file"
    fi

    local base_container_name="${2:-[parse_gc]}"
    local path_to_pdf_files="${3:?Specify the pdf file path}"
    local path_to_json_output="${4:?Specify the json output path}"

    local ingest_container_image="${BASE_JOB_IMAGE:-10.194.9.80:5000/gamechanger/core/dev-env:latest}"

    echo Cleaning up old containers...
    ( docker container rm -f $base_container_name || true ) &> /dev/null

    echo Running Job...
    (
        # main docker run to do the actual parsing
        docker run \
            --name $base_container_name \
            --user "$(id -u):$(id -g)" \
            --mount type=bind,source="$path_to_pdf_files",destination="/input" \
            --mount type=bind,source="$path_to_json_output",destination="/output" \
            --mount type=bind,source="$HOST_REPO_DIR",destination="/gamechanger" \
            --workdir "/gamechanger" \
            "$ingest_container_image" "$CONTAINER_PYTHON_CMD" -m common.document_parser pdf-to-json \
              -s "/input" \
              -d "/output" \
              -m "/input" \
              -c \
              -w \
              -p 12
    ) | tee -a "$local_job_log_file"
}

parse "$@"
exit $?
