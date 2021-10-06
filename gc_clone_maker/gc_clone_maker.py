import os
from pathlib import Path
import json
from textwrap import dedent

# from sqlalchemy.orm import query
from .config import Config
from dataPipelines.gc_db_utils.web.models import CloneMeta
from datetime import datetime as dt

from gc_clone_maker import config
import subprocess


# TODO
# query db for meta rows
# take a row and parse args needed out
# use args to write a config file
# run clone creation script with that config file

class CloneParams:
    def __init__(self, *_, **kwargs):
        self.__dict__.update(kwargs)

    source_agency_name: str
    metadata_creation_group: str = "pdf"
    clone_name: str
    elasticsearch_index: str
    data_source_name: str
    source_s3_prefix: str
    source_s3_bucket: str


class CloneMaker:

    def generate_clone(self):

        Config.connection_helper.init_web_db()
        with Config.connection_helper.web_db_session_scope('rw') as session:
            to_ingest = session.query(
                CloneMeta).filter_by(needs_ingest=True).one_or_none()

            if to_ingest:
                clone_params = self.make_clone_params(to_ingest=to_ingest)
                print(f'{clone_params.clone_name} ingest starting')
                print('Setting needs_ingest flag to False')
                to_ingest.needs_ingest = False
                session.commit()

            else:
                print('No clone_meta with needs_ingest set, returning')
                return

        print(clone_params.clone_name,
              "will be created, writing a config for it...")

        clone_config_path = self.write_config_file(cp=clone_params)

        # env_dict.update({"LC_ALL": "C.UTF-8", "LANG": "C.UTF-8"})

        cmd = ["bash", 'paasJobs/job_runner.sh', clone_config_path]
        print("Starting", f"`{' '.join(cmd)}`, with env:", os.environ)

        completed_process = subprocess.run(
            cmd, stdout=subprocess.PIPE, env=os.environ)

    @staticmethod
    def make_clone_params(to_ingest):
        params_needed = [
            # "source_agency_name",
            # "data_source_name",
            "metadata_creation_group",
            "clone_name",
            "source_s3_bucket",
            "source_s3_prefix",
            "elasticsearch_index"
        ]
        params = {}
        missing = []
        for key, val in to_ingest.__dict__.items():
            if key in params_needed:
                if val is None:
                    missing.append(key)
                else:
                    params[key] = val

        if missing:
            raise Exception(
                f'Missing required parameters to make a clone: {missing}')
        else:
            return CloneParams(**params)

    @staticmethod
    def write_config_file(cp: CloneParams) -> str:
        date = dt.now().strftime('%Y%m%d')
        config_text = dedent(f"""
            #!/usr/bin/env bash

            #####
            ## ## CRAWLER INGEST JOB CONFIG
            #####
            #
            ## USAGE (CRON or OTHERWISE):
            #     env <envvar1=val1 envvar2=val2 ...> <path-to/job_runner.sh> <path-to/this.conf.sh>
            #
            ## NOTE all env vars that don't have defaults must be exported ahead of time or passed via `env` command
            #
            ## MINIMAL EXAMPLE:
            #     env SLACK_HOOK_CHANNEL="#some-channel" SLACK_HOOK_URL="https://slack/hook" /app/job_runner.sh /app/somejob.conf.sh
            #

            readonly SCRIPT_PARENT_DIR="$( cd "$( dirname "${{BASH_SOURCE[0]}}" )" >/dev/null 2>&1 && pwd )"
            readonly REPO_DIR="$( cd "$SCRIPT_PARENT_DIR/../../../"  >/dev/null 2>&1 && pwd )"

            ## BASE JOB_CONF

            JOB_NAME="{cp.clone_name}_CLONE_S3_INGEST"
            JOB_SCRIPT="${{REPO_DIR}}/paasJobs/jobs/s3_ingest.sh"
            SEND_NOTIFICATIONS="yes"
            UPLOAD_LOGS="yes"
            SLACK_HOOK_CHANNEL="${{SLACK_HOOK_CHANNEL}}"
            SLACK_HOOK_URL="${{SLACK_HOOK_URL}}"
            S3_BASE_LOG_PATH_URL="${{S3_BASE_LOG_PATH_URL:-s3://advana-data-zone/bronze/gamechanger/data-pipelines/orchestration/logs/{cp.clone_name}-s3-ingest}}"
            AWS_DEFAULT_REGION="${{AWS_DEFAULT_REGION:-us-gov-west-1}}"
            CLEANUP="${{CLEANUP:-yes}}"
            TMPDIR="${{TMPDIR:-/data/tmp}}"
            VENV_ACTIVATE_SCRIPT="${{VENV_ACTIVATE_SCRIPT:-/opt/gc-venv-current/bin/activate}}"
            # PYTHONPATH="${{PYTHONPATH:-$REPO_DIR}}"

            ## JOB SPECIFIC CONF

            export ES_INDEX_NAME="{cp.elasticsearch_index.lower()}_{date}"
            export ES_ALIAS_NAME="{cp.elasticsearch_index.lower()}"

            export S3_RAW_INGEST_PREFIX="{cp.source_s3_prefix}" #pdf and metadata path
            export S3_PARSED_INGEST_PREFIX="${{S3_PARSED_INGEST_PREFIX:-}}"

            export METADATA_CREATION_GROUP="{cp.metadata_creation_group if cp.metadata_creation_group else ''}"

            export MAX_OCR_THREADS_PER_FILE="${{MAX_OCR_THREADS_PER_FILE:-2}}"
            export MAX_PARSER_THREADS="${{MAX_PARSER_THREADS:-16}}"
            export MAX_S3_THREADS="${{MAX_S3_THREADS:-32}}"

            export S3_BUCKET_NAME="{cp.source_s3_bucket}"

            export SKIP_NEO4J_UPDATE="${{SKIP_NEO4J_UPDATE:-yes}}"
            export SKIP_SNAPSHOT_BACKUP="${{SKIP_SNAPSHOT_BACKUP:-no}}"
            export SKIP_DB_BACKUP="${{SKIP_DB_BACKUP:-yes}}"
            export SKIP_DB_UPDATE="${{SKIP_DB_UPDATE:-yes}}"
            export SKIP_REVOCATION_UPDATE="${{SKIP_REVOCATION_UPDATE:-yes}}"
            export SKIP_THUMBNAIL_GENERATION="${{SKIP_THUMBNAIL_GENERATION:-yes}}"

            export CURRENT_SNAPSHOT_PREFIX="${{CURRENT_SNAPSHOT_PREFIX:-bronze/gamechanger/projects/{cp.clone_name}/}}"
            export BACKUP_SNAPSHOT_PREFIX="${{BACKUP_SNAPSHOT_PREFIX:-bronze/gamechanger/projects/{cp.clone_name}/backup/}}"
            export LOAD_ARCHIVE_BASE_PREFIX="${{LOAD_ARCHIVE_BASE_PREFIX:-bronze/gamechanger/projects/{cp.clone_name}/load-archive/}}"
            export DB_BACKUP_BASE_PREFIX="${{DB_BACKUP_BASE_PREFIX:-bronze/gamechanger/projects/{cp.clone_name}/backup/db/}}"

            export CLONE_OR_CORE="clone"

        """)
        print('*********** Config Made ************')
        print(config_text)
        print()
        filepath = Path(
            f'paasJobs/jobs/configs/clone_s3_generated_{cp.clone_name}.conf.sh')
        with open(filepath, 'w') as config_file:
            config_file.write(config_text)
        print('written to', str(filepath))
        return str(filepath)
