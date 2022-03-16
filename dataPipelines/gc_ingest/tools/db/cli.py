import click
from .utils import CoreDBManager, DBType
from pathlib import Path
import sys
import typing as t
from dataPipelines.gc_ingest.config import Config
from dataPipelines.gc_ingest.common_cli_options import pass_bucket_name_option
import functools
from enum import Enum
import datetime as dt


class ExportImportFileFormat(Enum):
    CSV = 'csv'


def common_options(f):
    @click.option(
        '--db',
        type=click.Choice([e.value for e in DBType]),
        required=True
    )
    @functools.wraps(f)
    def wf(*args, **kwargs):
        return f(*args, **kwargs)
    return wf


def common_backup_options(f):
    @click.option(
        '--download-dir',
        type=click.Path(exists=True, dir_okay=True, file_okay=False, resolve_path=True),
        help="Path to download dir. Uses temporary dir based on $TMPDIR if unset",
        required=False
    )
    @click.option(
        '--ts',
        type=click.DateTime(),
        help="Timestamp used to construct backup s3 path",
        default=Config.default_batch_timestamp_str
    )
    @functools.wraps(f)
    def wf(*args, **kwargs):
        return f(*args, **kwargs)
    return wf


def common_export_import_options(f):
    @click.option(
        '--format',
        type=click.Choice([e.value for e in ExportImportFileFormat]),
        default=ExportImportFileFormat.CSV.value,
        help="Export/Import file format",
        show_default=True
    )
    @click.option(
        '--schema',
        type=str,
        default='public',
        show_default=True
    )
    @functools.wraps(f)
    def wf(*args, **kwargs):
        return f(*args, **kwargs)
    return wf


def pass_core_db_cli_options(f):
    @click.option(
        '--db-backup-base-prefix',
        type=str,
        help="Base s3 prefix to where db backups are stored",
        required=True
    )
    @functools.wraps(f)
    def wf(*args, **kwargs):
        return f(*args, **kwargs)
    return wf


@click.group(name='db')
@pass_core_db_cli_options
@pass_bucket_name_option
@click.pass_context
def db_cli(
    ctx: click.Context,
    db_backup_base_prefix: str,
    bucket_name: str):
    """DB Tools"""
    ctx.obj = CoreDBManager(
        db_backup_base_prefix=db_backup_base_prefix,
        bucket_name=bucket_name
    )


pass_core_dbm = click.make_pass_decorator(CoreDBManager)


@db_cli.command(name='backup')
@common_backup_options
@common_options
@pass_core_dbm
def backup(dbm: CoreDBManager, db: str, download_dir: t.Optional[str], ts: dt.datetime) -> None:
    """Backup DB tables"""
    dbm.backup_all_tables(
        db_type=db,
        ts=ts,
        job_dir=download_dir or None
    )


@db_cli.command(name='restore')
@click.option(
    '--replace',
    type=bool,
    default=False,
    show_default=True,
    help="Wipe out destination tables before restoring them"
)
@common_backup_options
@common_options
@pass_core_dbm
def restore(dbm: CoreDBManager, db: str, ts: dt.datetime, download_dir: t.Optional[str], replace: bool) -> None:
    """Restore DB tables"""
    dbm.restore_all_tables(
        db_type=db,
        ts=ts,
        job_dir=download_dir or None,
        truncate_first=replace
    )


@db_cli.command(name='refresh')
@common_options
@pass_core_dbm
def refresh(dbm: CoreDBManager, db: str):
    """Refresh materialized DB tables"""
    print(f"Refreshing materialized tables in the '{db}' database ...", file=sys.stderr)
    dbm.refresh_materialized_tables(
        db_type=db
    )


@db_cli.command(name='export')
@click.option(
    '--table-or-view',
    type=str,
    required=True,
    help="Table or view to export"
)
@click.option(
    '--output-file',
    type=click.Path(dir_okay=False),
    required=True
)
@common_export_import_options
@common_options
@pass_core_dbm
def export_cmd(dbm: CoreDBManager, db: str, format: str, schema: str, table_or_view: str, output_file: str):
    """Export DB table/view data to file"""
    print(f"Exporting table/view {table_or_view} to {output_file}", file=sys.stderr)
    if ExportImportFileFormat(format) == ExportImportFileFormat.CSV:
        dbm.export_table_or_view(
            db_type=db,
            table_or_view=table_or_view,
            output_file=output_file,
            schema=schema
        )


@db_cli.command(name='import')
@click.option(
    '--table',
    type=str,
    help="Name of table where data will be imported",
    required=True
)
@click.option(
    '--input-file',
    type=click.Path(exists=True, dir_okay=False, file_okay=True),
    required=True
)
@common_export_import_options
@common_options
@pass_core_dbm
def import_cmd(dbm: CoreDBManager, db: str, format: str, schema: str, table: str, input_file: str) -> None:
    """Import DB table/view data from file"""
    print(f"Importing {input_file} to table {table}", file=sys.stderr)
    if ExportImportFileFormat(format) == ExportImportFileFormat.CSV:
        dbm.import_table(
            db_type=db,
            table=table,
            schema=schema,
            input_file=input_file
        )


@db_cli.command(name='dump')
@click.option(
    '--output-dir',
    type=click.Path(exists=True, dir_okay=True, file_okay=False),
    required=True
)
@click.option(
    '--overwrite',
    type=bool,
    default=False,
    show_default=True,
    help="Overwrite files that may exist in the output dir"
)
@click.option(
    '--format',
    type=click.Choice([e.value for e in ExportImportFileFormat]),
    default=ExportImportFileFormat.CSV.value,
    help="Export/Import file format",
    show_default=True
)
@common_options
@pass_core_dbm
def dump_cmd(dbm: CoreDBManager, db: str, format: str, output_dir: str, overwrite: bool) -> None:
    """Dump all tables that are part of normal backup to dir"""
    if ExportImportFileFormat(format) == ExportImportFileFormat.CSV:
        dbm.export_all_tables(
            db_type=db,
            export_base_dir=output_dir,
            clobber=overwrite
        )
