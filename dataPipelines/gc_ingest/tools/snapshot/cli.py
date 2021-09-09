import click
from pathlib import Path
from .utils import SnapshotManager, SnapshotType
from dataPipelines.gc_ingest.config import Config
from dataPipelines.gc_ingest.common_cli_options import pass_bucket_name_option
import functools
import datetime as dt
import json


def common_options(f):
    @click.option(
        '-t',
        '--snapshot-type',
        type=click.Choice([e.value for e in SnapshotType]),
        required=True
    )
    @functools.wraps(f)
    def wrapped_f(*args, **kwargs):
        return f(*args, **kwargs)
    return wrapped_f


def pass_core_snapshot_cli_options(f):
    @click.option(
        '--current-snapshot-prefix',
        type=str,
        help="S3 prefix where current snapshots live",
        required=True
    )
    @click.option(
        '--backup-snapshot-prefix',
        type=str,
        help="S3 prefix where backup snapshots live",
        required=True
    )
    @functools.wraps(f)
    def wf(*args, **kwargs):
        return f(*args, **kwargs)
    return wf


@click.group(name="snapshot")
@pass_core_snapshot_cli_options
@pass_bucket_name_option
@click.pass_context
def snapshot_cli(ctx: click.Context,
                 current_snapshot_prefix: str,
                 backup_snapshot_prefix: str,
                 bucket_name: str):
    """Tool for managing corpus data snapshots"""
    ctx.obj = SnapshotManager(
        current_doc_snapshot_prefix=current_snapshot_prefix,
        backup_doc_snapshot_prefix=backup_snapshot_prefix,
        bucket_name=bucket_name
    )


pass_sm = click.make_pass_decorator(SnapshotManager)


@snapshot_cli.command()
@click.option(
    '-d',
    '--dst-dir',
    help="Destination dir for the snapshot files",
    type=click.Path(
        dir_okay=True,
        file_okay=False,
        resolve_path=True
    ),
    required=True
)
@click.option(
    '--using-db',
    type=bool,
    default=False,
    show_default=True,
    help="Use DB to resolve which files should be downloaded"
)
@common_options
@pass_sm
def pull(sm: SnapshotManager, snapshot_type: str, dst_dir: str, using_db: bool) -> None:
    """Ingest from a local directory"""
    local_dst_dir_path = Path(dst_dir).resolve()
    local_dst_dir_path.mkdir(exist_ok=True)

    print("Downloading snapshot to disk")
    sm.pull_current_snapshot_to_disk(
        local_dir=local_dst_dir_path,
        snapshot_type=snapshot_type,
        using_db=using_db
    )


@snapshot_cli.command()
@click.option(
    '-s',
    '--src-dir',
    type=click.Path(exists=True, dir_okay=True, file_okay=False),
    required=True
)
@click.option(
    '--replace',
    type=bool,
    default=False,
    show_default=True,
    help="Replace all of current snapshot with this update"
)
@common_options
@pass_sm
def update(sm: SnapshotManager, snapshot_type: str, src_dir: str, replace: bool) -> None:
    """Update current snapshot using local files"""
    print("Updating current snapshot ...")
    sm.update_current_snapshot_from_disk(
        local_dir=src_dir,
        snapshot_type=snapshot_type,
        replace=replace
    )


@snapshot_cli.command()
@click.option(
    '--ts',
    type=click.DateTime(),
    help='Timestamp to use when creating backup prefix',
    default=Config.default_batch_timestamp_str
)
@common_options
@pass_sm
def backup(sm: SnapshotManager, snapshot_type: str, ts: dt.datetime) -> None:
    """Backup current snapshot to archive"""
    print(f"Backing up current {snapshot_type} snapshot ...")
    sm.backup_current_snapshot(
        snapshot_type=snapshot_type,
        snapshot_ts=ts
    )


@snapshot_cli.command()
@click.option(
    '--ts',
    type=click.DateTime(),
    help='Timestamp to use when restoring backup prefix',
    default=Config.default_batch_timestamp_str
)
@common_options
@pass_sm
def restore(sm: SnapshotManager, snapshot_type: str, ts: dt.datetime) -> None:
    """Restore current snapshot from archived one"""
    print(f"Restoring current {snapshot_type} snapshot ...")
    sm.restore_current_snapshot(
        snapshot_type=snapshot_type,
        snapshot_ts=ts
    )


@snapshot_cli.command(name='recreate-web-snapshot')
@pass_sm
def recreate_web_snapshot(sm: SnapshotManager):
    """Recreate snapshot table in the web db using latest snapshot in orch db"""
    print("Recreating web db snapshot ... ")
    sm.recreate_web_db_snapshot()
    print("[OK] Web db snapshot refreshed.")

def remove_docs_from_current_snapshot(sm: SnapshotManager, removal_list: list ):

    for filename in removal_list:
        sm.delete_from_current_snapshot(filename=filename)

@snapshot_cli.command()
@pass_sm
@click.option(
        '--input-json-path',
        type=str,
        help="Input JSON list path, this should resemble the metadata, at least having a 'doc_name' field " +
             "and a 'downloadable_items'.'doc_type' field",
        required=True
    )
def remove_docs_from_s3(sm: SnapshotManager, input_json_path: str ):
    input_json = Path(input_json_path).resolve()
    if not input_json.exists():
        print("No valid input json")
        return

    removal_list = []

    print("REMOVING DOCS FROM S3")
    with input_json.open(mode="r") as f:
        for json_str in f.readlines():
            if not json_str.strip():
                continue
            else:
                try:
                    j_dict = json.loads(json_str)
                except json.decoder.JSONDecodeError:
                    print("Encountered JSON decode error while parsing crawler output.")
                    continue
                filename = Path(j_dict.get("filename",
                                           j_dict["doc_name"] +
                                           "." +
                                           j_dict["downloadable_items"].pop()["doc_type"]))
                removal_list.append(filename)

    remove_docs_from_current_snapshot(
        sm=sm,
        removal_list=removal_list
    )