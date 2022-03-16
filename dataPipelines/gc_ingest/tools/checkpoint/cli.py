import click
from dataPipelines.gc_ingest.tools.checkpoint.utils import CheckpointManager
from dataPipelines.gc_ingest.common_cli_options import pass_bucket_name_option
import datetime as dt
import functools


def pass_core_checkpoint_cli_options(f):
    @click.option(
        '--checkpoint-file-path',
        type=str,
        required=True,
        help="Path to s3 object where checkpoint timestamp is stored"
    )
    @click.option(
        '--checkpointed-dir-path',
        type=str,
        required=True,
        help="Path to s3 prefix at base of the checkpointed paths"
    )
    @click.option(
        '--checkpoint-ready-marker',
        type=str,
        required=False,
        help="Name of the file that marks checkpointed dir ready for processing"
    )
    @functools.wraps(f)
    def wf(*args, **kwargs):
        return f(*args, **kwargs)
    return wf


@click.group(name='checkpoint')
@pass_core_checkpoint_cli_options
@pass_bucket_name_option
@click.pass_context
def checkpoint_cli(ctx: click.Context, checkpoint_file_path: str, checkpointed_dir_path: str, checkpoint_ready_marker: str, bucket_name: str):
    "Tools for handling checkpointed jobs"
    ctx.obj = CheckpointManager(
        checkpoint_file_path=checkpoint_file_path,
        checkpointed_dir_path=checkpointed_dir_path,
        bucket_name=bucket_name,
        checkpoint_ready_marker=checkpoint_ready_marker or None
    )


pass_cpm = click.make_pass_decorator(CheckpointManager)


@checkpoint_cli.command()
@click.argument(
    'checkpoint_choice',
    type=click.Choice(['current','next','remaining'])
)
@click.option(
    '--limit',
    type=int,
    default=0
)
@pass_cpm
def get(cpm: CheckpointManager, checkpoint_choice: str, limit: int):
    """Get checkpointed paths"""

    prefixes = []
    if checkpoint_choice == 'current':
        prefix = cpm.current_prefix
        if prefix:
            prefixes.append(prefix)
    elif checkpoint_choice == 'next':
        prefix = cpm.next_prefix
        if prefix:
            prefixes.append(prefix)
    else:
        prefixes = cpm.remaining_prefixes[:limit if limit > 0 else None]

    if prefixes:
        for p in prefixes:
            print(f"{cpm.bucket_name}/{p.prefix_path}")


@checkpoint_cli.command()
@click.argument("timestamp", type=click.DateTime())
@pass_cpm
def set(cpm: CheckpointManager, timestamp: dt.datetime):
    """Set checkpoint"""
    cpm.current_checkpoint_ts = timestamp


def pass_advance_checkpoint_option(f):
    @click.option(
        '--advance-checkpoint',
        type=bool,
        default=False,
        help="Whether to advance the checkpoint at the end"
    )
    @functools.wraps(f)
    def wf(*args, **kwargs):
        return f(*args, **kwargs)
    return wf


@checkpoint_cli.command()
@click.argument(
    'checkpoint_choice',
    type=click.Choice(['next','remaining'])
)
@click.option(
    '--limit',
    type=int,
    default=0
)
@click.option(
    '--output-dir',
    type=click.Path(exists=True, dir_okay=True, file_okay=False, resolve_path=True),
    required=True
)
@pass_advance_checkpoint_option
@pass_cpm
def pull(cpm: CheckpointManager,
         checkpoint_choice: str,
         limit: int, output_dir: str,
         advance_checkpoint: bool):
    """Pull checkpoint to local disk"""
    if checkpoint_choice == 'next':
        with cpm.checkpoint_download_manager(
            base_download_dir=output_dir,
            advance_checkpoint=advance_checkpoint,
            limit=1
        ) as downloaded_prefixes:
            for dp in downloaded_prefixes:
                print(str(dp.local_path.resolve()))
    else:
        with cpm.checkpoint_download_manager(
            base_download_dir=output_dir,
            advance_checkpoint=advance_checkpoint,
            limit=limit if limit > 0 else None
        ) as downloaded_prefixes:
            for dp in downloaded_prefixes:
                print(str(dp.local_path.resolve()))
