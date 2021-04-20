from dataPipelines.gc_db_utils.utils import export_to_csv, import_from_csv, truncate_table, check_if_table_or_view_exists
from dataPipelines.gc_db_utils.orch.utils import recreate_tables_and_views as recreate_orch_db_schema
from dataPipelines.gc_db_utils.web.utils import recreate_tables_and_views as recreate_web_db_schema, seed_dafa_charter_map
from enum import Enum
import typing as t
from dataPipelines.gc_ingest.config import Config
from common.utils.s3 import S3Utils
from common.utils.parsers import parse_timestamp
import datetime as dt
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from dataPipelines.gc_db_utils.web.models import SnapshotEntry
from dataPipelines.gc_db_utils.web.schemas import SnapshotEntrySchema
from dataPipelines.gc_db_utils.orch.models import SnapshotViewEntry


class DBType(Enum):
    ORCH = 'orch'
    WEB = 'web'


class CoreDBManager:
    # TODO: see if this entire tool/cli should be integrated into dataPipelines.gc_db_utils package
    BACKUP_TABLES_MAP: t.Dict[DBType, t.Set[str]] = {
        DBType.ORCH: {'versioned_docs', 'publications', 'pipeline_jobs'},
        DBType.WEB: {'dafa_charter_map', 'gc_document_corpus_snapshot'}
    }

    def __init__(self,
                 db_backup_base_prefix: str,
                 bucket_name: str = Config.s3_bucket,
                 **ignored_kwargs):
        """ Core orch/web table tools
        :param db_backup_base_prefix: S3 base prefix for storing/restoring db backup
        :param bucket_name: S3 bucket name
        """
        self.bucket_name = bucket_name
        self.ch = Config.connection_helper
        self.s3u = S3Utils(ch=self.ch, bucket=self.bucket_name)
        self.db_backup_base_prefix = self.s3u.format_as_prefix(db_backup_base_prefix)
        self.ch.init_dbs()

    def get_db_engine(self, db_type: t.Union[DBType, str]):
        """Get db engine appropriate for db_type"""
        db_type = DBType(db_type)
        return {
            DBType.WEB: self.ch.web_db_engine,
            DBType.ORCH: self.ch.orch_db_engine
        }[db_type]

    def get_backup_prefix(self, db_type: t.Union[DBType, str], ts: t.Union[dt.datetime, str]) -> str:
        """Get S3 backup prefix for given db_type and timestamp"""
        db_type = DBType(db_type)
        ts = parse_timestamp(ts, raise_parse_error=True)
        ts_str = ts.strftime(Config.TIMESTAMP_FORMAT)

        return {
            DBType.WEB: self.db_backup_base_prefix + DBType.WEB.value + '/' + ts_str,
            DBType.ORCH: self.db_backup_base_prefix + DBType.ORCH.value + '/' + ts_str
        }[db_type]

    def truncate_backup_tables(self, db_type: t.Union[DBType, str]) -> None:
        """Truncates all tables configured for backup of given db"""
        db_type = DBType(db_type)
        db_engine = self.get_db_engine(db_type=db_type)

        for table_name in self.BACKUP_TABLES_MAP[db_type]:
            print(f"Truncating Table:{table_name} ... ")
            truncate_table(
                db_engine=db_engine,
                table=table_name,
                cascade=True
            )

    def recreate_tables_and_views(self, db_type: t.Union[DBType, str]) -> None:
        """Recreate schema for given db type (wipes out existing data)"""
        db_type = DBType(db_type)
        if db_type == DBType.WEB:
            recreate_web_db_schema()
        elif db_type == DBType.ORCH:
            recreate_orch_db_schema()
        else:
            raise RuntimeError("This code should not be reachable")

    def _get_orch_db_snapshot_entries(self, scroll_window: int = 1000) -> t.Iterable[SnapshotViewEntry]:
        """Iterate through all snapshot entries
        :param scroll_window: How many entries to fetch from db at any given time
        :return: Iterable of snapshot entries
        """
        with self.ch.orch_db_session_scope('ro') as session:
            for obj in session.query(SnapshotViewEntry).yield_per(scroll_window):
                yield obj

    # TODO: remove recreate db snapshot functions/cli out of dataPipelines.gc_ingest.tools.snapshot
    # TODO: create a more generic function for materializing views from one db to another with optional field remapping
    def _refresh_web_db_snapshot(self) -> None:
        """Recreate snapshot table in web db using snapshot view from orch db"""

        # TODO: see if we can use csv export/import with io buffer instead of this
        # TODO: See if we can do atomic update instead of truncate to improve availability
        with Config.connection_helper.web_db_session_scope('rw') as session:
            web_db_entries = [
                SnapshotEntry(**{k: getattr(orch_entry, k) for k, _ in SnapshotEntrySchema.__dict__.items() if not k.startswith('_')})
                for orch_entry in self._get_orch_db_snapshot_entries()
            ]

            if not web_db_entries:
                return

            truncate_table(
                db_engine=self.get_db_engine(db_type=DBType.WEB),
                table=str(SnapshotEntry.__tablename__),
                cascade=True
            )
            session.add_all(web_db_entries)

    def refresh_materialized_tables(self, db_type: t.Union[DBType, str]) -> None:
        """Refreshes materialized or seeded tables/views"""
        db_type = DBType(db_type)

        if db_type == DBType.ORCH:
            pass
        elif db_type == DBType.WEB:
            self._refresh_web_db_snapshot()
            seed_dafa_charter_map(engine=self.get_db_engine(db_type=db_type))

    def refresh_materialized_tables_for_all_dbs(self) -> None:
        """Refreshes materialized or seeded tables/views for all dbs"""
        for dbt in DBType:
            self.refresh_materialized_tables(db_type=dbt)

    def export_table_or_view(self,
                             db_type: t.Union[DBType, str],
                             table_or_view: str,
                             output_file: t.Union[Path, str],
                             schema: str = 'public'):
        """Import table from file
        :param db_type: db type - web/orch
        :param table: table_or_view to read from
        :param output_file: file to export to
        :param schema: table_or_view schema
        """
        db_type = DBType(db_type)
        db_engine = self.get_db_engine(db_type=db_type)
        output_file = Path(output_file).resolve()

        if not check_if_table_or_view_exists(db_engine=db_engine, table_or_view=table_or_view, schema=schema):
            raise LookupError(f"Can't export from '{schema}.{table_or_view}' - does not exist in '{db_type.value}' db.")

        export_to_csv(
            db_engine=db_engine,
            output_file=output_file,
            table_or_view=table_or_view,
            schema=schema
        )

    def import_table(self,
                     db_type: t.Union[DBType, str],
                     table: str,
                     input_file: t.Union[Path, str],
                     schema: str = 'public'):
        """Import table from file
        :param db_type: db type - web/orch
        :param table: table to write into
        :param input_file: file to import from
        :param schema: table schema
        """
        db_type = DBType(db_type)
        db_engine = self.get_db_engine(db_type=db_type)
        input_file = Path(input_file).resolve()

        if not check_if_table_or_view_exists(db_engine=db_engine, table_or_view=table, schema=schema):
            raise LookupError(f"Can't load into '{schema}.{table}' - does not exist in '{db_type.value}' db.")

        import_from_csv(
            db_engine=db_engine,
            input_file=input_file,
            table=table,
            schema=schema
        )

    def export_all_tables(self,
                          db_type: t.Union[DBType, str],
                          export_base_dir: t.Union[Path, str],
                          clobber: bool = False) -> None:
        """Export all tables that are part of normal backup
        :param db_type: database type orch/web
        :param export_base_dir: output directory
        :param clobber: whether to overwrite existing files
        """
        db_type = DBType(db_type)
        export_base_dir = Path(export_base_dir).resolve()
        backup_tables = self.BACKUP_TABLES_MAP[db_type]

        if not export_base_dir.is_dir():
            raise ValueError(f"Given export dir doesn't exist: {export_base_dir!s}")

        for table_name in backup_tables:
            output_file = Path(export_base_dir, table_name + ".csv")
            if (not clobber) and output_file.exists():
                raise FileExistsError(f"There's already a file at this location: {output_file!s}")

            print(f"Exporting Table:{table_name} to {output_file!s}", file=sys.stderr)
            self.export_table_or_view(
                db_type=db_type,
                table_or_view=table_name,
                output_file=output_file
            )

    def import_all_tables(self, db_type: t.Union[DBType, str], import_base_dir: t.Union[Path, str]):
        db_type = DBType(db_type)
        import_base_dir = Path(import_base_dir).resolve()

        if not import_base_dir.is_dir():
            raise ValueError(f"Given import dir doesn't exist: {import_base_dir!s}")

        restoreable_tables = self.BACKUP_TABLES_MAP[db_type]
        importable_files = [p for p in import_base_dir.glob("*.csv")]
        importable_tables = [p.stem for p in importable_files]

        if not restoreable_tables >= set(importable_tables):
            expected_files = [t + '.csv' for t in restoreable_tables]
            raise ValueError(f"Could not find appropriate backup files in the dir. "
                               f"- looking for {expected_files}, but found these instead: {[p.name for p in importable_files]}")

        for table_name, import_file_path in ((p.stem, p) for p in importable_files if p.stem in restoreable_tables):
            print(f"Importing Table:{table_name} from {import_file_path!s}", file=sys.stderr)
            self.import_table(
                db_type=db_type,
                table=table_name,
                input_file=import_file_path
            )

    def backup_all_tables(self,
                          db_type: t.Union[DBType, str],
                          ts: t.Union[dt.datetime, str],
                          job_dir: t.Optional[t.Union[Path, str]] = None) -> None:
        """Backup all tables for given db_type to S3
        :param db_type: type of db - web/orch
        :param ts: backup timestamp that determines s3 backup path
        :param job_dir: directory used to store downloaded files - temp dir by default
        """
        db_type = DBType(db_type)
        ts = parse_timestamp(ts, raise_parse_error=True)
        backup_prefix = self.get_backup_prefix(db_type=db_type, ts=ts)

        if self.s3u.prefix_exists(backup_prefix):
            raise ValueError(f"Cannot backup to given timestamped prefix because it already exists: {backup_prefix}")

        try:
            td = None
            if job_dir:
                job_dir = Path(job_dir).resolve()
                job_dir.mkdir(exist_ok=True)
            else:
                td = TemporaryDirectory()
                job_dir = Path(td.name)

            print(f"Backing up tables to S3 {backup_prefix}.", file=sys.stderr)
            self.export_all_tables(db_type=db_type, export_base_dir=job_dir)
            self.s3u.upload_dir(local_dir=job_dir, prefix_path=backup_prefix)
        finally:
            if td:
                td.cleanup()

    def backup_all_tables_for_all_dbs(self,
                                      ts: t.Union[dt.datetime, str],
                                      job_dir: t.Optional[t.Union[Path, str]] = None) -> None:
        """Backup all tables for all databases"""
        ts = parse_timestamp(ts, raise_parse_error=True)

        for dbt in DBType:
            td = None
            try:
                if job_dir:
                    job_dir = Path(job_dir).resolve()
                    backup_job_dir = Path(job_dir, dbt.value)
                    backup_job_dir.mkdir(exist_ok=False)
                else:
                    td = TemporaryDirectory()
                    backup_job_dir = Path(td.name)

                self.backup_all_tables(
                    db_type=dbt,
                    ts=ts,
                    job_dir=backup_job_dir
                )
            finally:
                if td:
                    td.cleanup()

    def restore_all_tables(self,
                           db_type: t.Union[DBType, str],
                           ts: t.Union[dt.datetime, str],
                           job_dir: t.Optional[t.Union[Path, str]] = None,
                           truncate_first: bool = False) -> None:
        """Restore all tables for db_type from given backup timestamp
        :param ts: backup timestamp that determines s3 backup path
        :param db_type: DB type - web/orch
        :param job_dir: directory used to store downloaded files - temp dir by default
        :param truncate_first: whether to truncate target db tables before importing data
        """
        db_type = DBType(db_type)
        ts = parse_timestamp(ts, raise_parse_error=True)
        backup_prefix = self.get_backup_prefix(db_type=db_type, ts=ts)

        if not self.s3u.prefix_exists(backup_prefix):
            raise ValueError(f"There is no backup at given prefix to import: {backup_prefix}")

        try:
            td = None
            if job_dir:
                job_dir = Path(job_dir).resolve()
                job_dir.mkdir(exist_ok=True)
            else:
                td = TemporaryDirectory()
                job_dir = Path(td.name)

            print(f"Restoring from backups at {backup_prefix}.", file=sys.stderr)
            self.s3u.download_dir(local_dir=job_dir, prefix_path=backup_prefix)
            if truncate_first:
                print("Truncating tables before import ...", file=sys.stderr)
                self.truncate_backup_tables(db_type=db_type)
            self.import_all_tables(db_type=db_type, import_base_dir=job_dir)
        finally:
            if td:
                td.cleanup()

    def restore_all_tables_for_all_dbs(self,
                                       ts: t.Union[dt.datetime, str],
                                       job_dir: t.Optional[t.Union[Path, str]] = None,
                                       truncate_first: bool = False) -> None:
        """Restore all tables for all databases"""
        ts = parse_timestamp(ts, raise_parse_error=True)

        for dbt in DBType:
            td = None
            try:
                if job_dir:
                    job_dir = Path(job_dir).resolve()
                    restore_job_dir = Path(job_dir, dbt.value)
                    restore_job_dir.mkdir(exist_ok=False)
                else:
                    td = TemporaryDirectory()
                    restore_job_dir = Path(td.name)

                self.restore_all_tables(
                    db_type=dbt,
                    ts=ts,
                    job_dir=restore_job_dir,
                    truncate_first=truncate_first
                )
            finally:
                if td:
                    td.cleanup()