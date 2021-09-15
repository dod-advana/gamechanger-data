import click
from dataPipelines.gc_ingest.tools.checkpoint.cli import pass_core_checkpoint_cli_options as pass_clone_checkpoint_cli_options
from dataPipelines.gc_ingest.tools.checkpoint.cli import pass_advance_checkpoint_option
from dataPipelines.gc_ingest.tools.checkpoint.utils import CheckpointManager
from dataPipelines.gc_ingest.tools.snapshot.utils import SnapshotManager
from dataPipelines.gc_ingest.tools.snapshot.cli import pass_core_snapshot_cli_options as pass_clone_snapshot_cli_options
from dataPipelines.gc_ingest.tools.load.utils import LoadManager
from dataPipelines.gc_ingest.tools.load.cli import pass_core_load_cli_options as pass_clone_load_cli_options
from dataPipelines.gc_elasticsearch_publisher.gc_elasticsearch_publisher import ConfiguredElasticsearchPublisher
from dataPipelines.gc_neo4j_publisher.utils import Neo4jJobManager
from dataPipelines.gc_ingest.tools.db.utils import DBType
from dataPipelines.gc_ingest.tools.db.utils import CoreDBManager as CloneDBManager
from dataPipelines.gc_ingest.tools.db.cli import pass_core_db_cli_options as pass_clone_db_cli_options
from dataPipelines.gc_ingest.common_cli_options import pass_bucket_name_option
from dataPipelines.gc_crawler_status_tracker.gc_crawler_status_tracker import CrawlerStatusTracker
from dataPipelines.gc_manual_metadata.gc_manual_metadata import ManualMetadata
from dataPipelines.gc_thumbnails.utils import ThumbnailsCreator
from pathlib import Path
import datetime as dt
from enum import Enum
import pydantic as pyd
import typing as t
import functools
import multiprocessing as mp

NonBlankString = t.NewType('NonBlankString', pyd.constr(
    strip_whitespace=True, min_length=1))
StrippedString = t.NewType('StrippedString', pyd.constr(strip_whitespace=True))


class IngestType(Enum):
    CHECKPOINT = 'checkpoint'
    S3 = 's3'
    LOCAL = 'local'


class IngestConfig(pyd.BaseModel):
    class Config:
        arbitrary_types_allowed = True
        extra = 'allow'


class CloneIngestConfig(IngestConfig):
    job_dir: NonBlankString
    crawler_output: t.Optional[NonBlankString]
    batch_timestamp: dt.datetime
    bucket_name: NonBlankString
    load_archive_base_prefix: NonBlankString
    db_backup_base_prefix: NonBlankString
    index_name: NonBlankString
    alias_name: t.Optional[StrippedString]
    max_threads: pyd.PositiveInt
    max_threads_neo4j: pyd.PositiveInt
    max_ocr_threads: pyd.PositiveInt
    max_s3_threads: pyd.PositiveInt
    skip_neo4j_update: bool = False
    skip_snapshot_backup: bool = False
    skip_db_backup: bool = False
    skip_db_update: bool = False
    skip_revocation_update: bool = False
    skip_es_revocation: bool = False
    skip_thumbnail_generation: bool = True
    current_snapshot_prefix: NonBlankString
    backup_snapshot_prefix: NonBlankString
    infobox_dir: t.Optional[StrippedString] = None
    es_mapping_file: t.Optional[StrippedString] = None

    @property
    def snapshot_manager(self) -> SnapshotManager:
        if hasattr(self, '_snapshot_manager'):
            return self._snapshot_manager

        self._snapshot_manager = SnapshotManager(
            current_doc_snapshot_prefix=self.current_snapshot_prefix,
            backup_doc_snapshot_prefix=self.backup_snapshot_prefix,
            bucket_name=self.bucket_name
        )
        return self._snapshot_manager

    @property
    def download_base_dir(self) -> Path:
        if hasattr(self, '_download_base_dir'):
            return self._download_base_dir

        self._download_base_dir = Path(self.job_dir, 'downloads')
        self._download_base_dir.mkdir(exist_ok=False)
        return self._download_base_dir

    @property
    def raw_doc_base_dir(self) -> Path:
        if hasattr(self, '_raw_doc_base_dir'):
            return self._raw_doc_base_dir

        self._raw_doc_base_dir = Path(self.job_dir, 'raw_docs')
        self._raw_doc_base_dir.mkdir(exist_ok=False)
        return self._raw_doc_base_dir

    @property
    def parsed_doc_base_dir(self) -> Path:
        if hasattr(self, '_parsed_doc_base_dir'):
            return self._parsed_doc_base_dir

        self._parsed_doc_base_dir = Path(self.job_dir, 'parsed_docs')
        self._parsed_doc_base_dir.mkdir(exist_ok=False)
        return self._parsed_doc_base_dir

    @property
    def db_backup_dir(self) -> Path:
        if hasattr(self, '_db_backup_dir'):
            return self._db_backup_dir

        self._db_backup_dir = Path(self.job_dir, 'db_backups')
        self._db_backup_dir.mkdir(exist_ok=False)
        return self._db_backup_dir

    @property
    def load_manager(self) -> LoadManager:
        if hasattr(self, '_load_manager'):
            return self._load_manager

        self._load_manager = LoadManager(
            load_archive_base_prefix=self.load_archive_base_prefix,
            bucket_name=self.bucket_name
        )
        return self._load_manager

    @property
    def thumbnail_doc_base_dir(self) -> Path:
        if hasattr(self, '_thumbnail_doc_base_dir'):
            return self._thumbnail_doc_base_dir

        self._thumbnail_doc_base_dir = Path(self.job_dir, 'thumbnails')
        self._thumbnail_doc_base_dir.mkdir(exist_ok=False)
        return self._thumbnail_doc_base_dir

    @property
    def es_publisher(self) -> ConfiguredElasticsearchPublisher:
        if hasattr(self, '_es_publisher'):
            return self._es_publisher

        self._es_publisher = ConfiguredElasticsearchPublisher(
            ingest_dir=self.parsed_doc_base_dir,
            index_name=self.index_name,
            mapping_file=self.es_mapping_file,
            alias=self.alias_name
        )
        return self._es_publisher

    @property
    def crawler_status_tracker(self) -> CrawlerStatusTracker:
        if hasattr(self, '_crawler_status_tracker'):
            return self._crawler_status_tracker

        self._crawler_status_tracker = CrawlerStatusTracker(
            input_json=self.crawler_output
        )
        return self._crawler_status_tracker

    @property
    def neo4j_job_manager(self) -> Neo4jJobManager:
        if hasattr(self, '_neo4j_job_manager'):
            return self._neo4j_job_manager

        self._neo4j_job_manager = Neo4jJobManager()
        return self._neo4j_job_manager

    @property
    def clone_db_manager(self) -> CloneDBManager:
        if hasattr(self, '_clone_db_manager'):
            return self._clone_db_manager

        self._clone_db_manager = CloneDBManager(
            db_backup_base_prefix=self.db_backup_base_prefix,
            bucket_name=self.bucket_name
        )
        return self._clone_db_manager

    @property
    def thumbnail_job_manager(self) -> ThumbnailsCreator:
        if hasattr(self, '_thumbnail_job_manager'):
            return self._thumbnail_job_manager

        self._thumbnail_job_manager = ThumbnailsCreator(
            input_directory=self.raw_doc_base_dir,
            output_directory=self.thumbnail_doc_base_dir,
            max_workers=self.max_threads
        )
        return self._thumbnail_job_manager

    @staticmethod
    def pass_options(f):
        @click.option(
            '--skip-neo4j-update',
            type=bool,
            default=False,
            help="Skip step to update Neo4J db",
            show_default=True
        )
        @click.option(
            '--skip-snapshot-backup',
            type=bool,
            default=False,
            help="Skip step to backup snapshots to s3",
            show_default=True
        )
        @click.option(
            '--skip-db-backup',
            type=bool,
            default=False,
            help="Skip step to backup db tables to s3",
            show_default=True
        )
        @click.option(
            '--skip-db-update',
            type=bool,
            default=False,
            help="Skip db updates during the load and revocations",
            show_default=True
        )
        @click.option(
            '--skip-revocation-update',
            type=bool,
            default=False,
            help="Skip adding revocations for db and es",
            show_default=True
        )
        @click.option(
            '--skip-es-revocation',
            type=bool,
            default=False,
            help="Skip adding revocations updates to es, will still update db",
            show_default=True
        )
        @click.option(
            '--skip-thumbnail-generation',
            type=bool,
            required=False,
            default=True,
            help="Whether or not to generate png of first page of pdf",
            show_default=True
        )
        @click.option(
            '--batch-timestamp',
            type=click.DateTime(),
            required=True,
            help="Load/Backup timestamp for this job"
        )
        @click.option(
            '--index-name',
            type=str,
            required=True,
            help="Name of ES index"
        )
        @click.option(
            '--alias-name',
            type=str,
            required=False,
            default="",
            help="Name of ES Alias"
        )
        @click.option(
            '--max-threads',
            type=int,
            required=False,
            default=mp.cpu_count(),
            show_default=True,
            help="Number of threads PER JOB to use for parsing/updating-neo4j"
        )
        @click.option(
            '--max-threads-neo4j',
            type=int,
            required=False,
            default=mp.cpu_count(),
            show_default=True,
            help="Number of threads PER JOB to use for parsing/updating-neo4j"
        )
        @click.option(
            '--max-ocr-threads',
            type=int,
            required=False,
            default=mp.cpu_count(),
            show_default=True,
            help="Number of threads PER FILE to use for OCR"
        )
        @click.option(
            '--max-s3-threads',
            type=int,
            required=False,
            default=mp.cpu_count(),
            show_default=True,
            help="Number of threads PER FILE to use for s3 uploads/downloads"
        )
        @click.option(
            '--crawler-output',
            type=click.Path(exists=False, dir_okay=False,
                            file_okay=True, resolve_path=True),
            help="Path to crawler output json file"
        )
        @click.option(
            '--job-dir',
            type=click.Path(exists=True, dir_okay=True,
                            file_okay=False, resolve_path=True),
            help="Path to job dir (should be empty, usually)"
        )
        @click.option(
            '--infobox-dir',
            help='Directory path of where to write the infobox.json files',
            type=click.Path(resolve_path=True, exists=True,
                            dir_okay=True, file_okay=False),
            required=False
        )
        @click.option(
            '--es-mapping-file',
            type=click.Path(exists=True, dir_okay=False,
                            file_okay=True, resolve_path=True),
            required=False,
            help="Path to a non-default es mapping file"
        )
        @pass_clone_snapshot_cli_options
        @pass_clone_db_cli_options
        @pass_clone_load_cli_options
        @pass_bucket_name_option
        @functools.wraps(f)
        def wf(*args, **kwargs):
            return f(*args, **kwargs)
        return wf


class CheckpointIngestConfig(CloneIngestConfig):
    checkpoint_file_path: NonBlankString
    checkpointed_dir_path: NonBlankString
    checkpoint_ready_marker: t.Optional[StrippedString]
    advance_checkpoint: bool = False
    checkpoint_limit: int = -1

    @property
    def checkpoint_manager(self) -> CheckpointManager:
        if hasattr(self, '_checkpoint_manager'):
            return self._checkpoint_manager

        self._checkpoint_manager = CheckpointManager(
            checkpoint_file_path=self.checkpoint_file_path,
            checkpointed_dir_path=self.checkpointed_dir_path,
            advance_checkpoint=self.advance_checkpoint,
            checkpoint_ready_marker=self.checkpoint_ready_marker,
            limit=self.checkpoint_limit if self.checkpoint_limit > 0 else None
        )
        return self._checkpoint_manager

    @staticmethod
    def pass_options(f):
        @click.option(
            '--checkpoint-limit',
            type=int,
            default=-1,
            help="Number of checkpoints to process this run"
        )
        @pass_clone_checkpoint_cli_options
        @pass_advance_checkpoint_option
        @functools.wraps(f)
        def wf(*args, **kwargs):
            return f(*args, **kwargs)
        return wf

    @staticmethod
    def from_clone_config(clone_config: CloneIngestConfig, other_config_kwargs: t.Dict[str, t.Any]) -> 'CheckpointIngestConfig':
        return CheckpointIngestConfig(**clone_config.dict(), **other_config_kwargs)


class S3IngestConfig(CloneIngestConfig):
    s3_raw_ingest_prefix: NonBlankString
    s3_parsed_ingest_prefix: t.Optional[StrippedString]
    metadata_creation_group: t.Optional[StrippedString]

    @staticmethod
    def pass_options(f):
        @click.option(
            '--s3-raw-ingest-prefix',
            type=str,
            help="S3 path with raw files to process (pdf + metadata)",
            required=True
        )
        @click.option(
            '--s3-parsed-ingest-prefix',
            type=str,
            help="S3 path with parsed files to process (json)",
            required=False
        )
        @click.option(
            '--metadata-creation-group',
            type=str,
            help="Document grouping to model metadata, if empty string or not assigned, no metadata will be created.",
            required=False
        )
        @functools.wraps(f)
        def wf(*args, **kwargs):
            return f(*args, **kwargs)
        return wf

    @property
    def metadata_creater(self) -> ManualMetadata:
        if hasattr(self, '_metadata_creater'):
            return self._metadata_creater
        if self.metadata_creation_group:
            self._metadata_creater = ManualMetadata(
                input_directory=self.raw_doc_base_dir,
                document_group=self.metadata_creation_group
            )
        return self._metadata_creater

    @staticmethod
    def from_clone_config(clone_config: CloneIngestConfig, other_config_kwargs=t.Dict[str, t.Any]) -> 'S3IngestConfig':
        return S3IngestConfig(**clone_config.dict(), **other_config_kwargs)


class LocalIngestConfig(CloneIngestConfig):
    local_raw_ingest_dir: pyd.DirectoryPath
    local_parsed_ingest_dir: t.Optional[pyd.DirectoryPath]

    @staticmethod
    def pass_options(f):
        @click.option(
            '--local-raw-ingest-dir',
            type=str,
            help="Local path with raw files to process (pdf + metadata)",
            required=True
        )
        @click.option(
            '--local-parsed-ingest-dir',
            type=str,
            help="Local path with parsed files to process (json)"
        )
        @functools.wraps(f)
        def wf(*args, **kwargs):
            return f(*args, **kwargs)
        return wf

    @staticmethod
    def from_clone_config(clone_config: CloneIngestConfig, other_config_kwargs=t.Dict[str, t.Any]) -> 'LocalIngestConfig':
        return LocalIngestConfig(**clone_config.dict(), **other_config_kwargs)

    @property
    def raw_doc_base_dir(self) -> Path:
        return self.local_raw_ingest_dir

    @property
    def parsed_doc_base_dir(self) -> Path:
        if hasattr(self, '_parsed_doc_base_dir'):
            return self._parsed_doc_base_dir

        self._parsed_doc_base_dir = self.local_parsed_ingest_dir or Path(
            self.job_dir, 'parsed_docs')
        self._parsed_doc_base_dir.mkdir(exist_ok=True)
        return self._parsed_doc_base_dir

    @property
    def db_backup_dir(self) -> Path:
        if hasattr(self, '_db_backup_dir'):
            return self._db_backup_dir

        self._db_backup_dir = Path(self.job_dir, 'db_backups')
        self._db_backup_dir.mkdir(exist_ok=False)
        return self._db_backup_dir
