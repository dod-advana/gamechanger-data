import click
from dataPipelines.gc_ingest.config import Config
from dataPipelines.gc_ingest.pipelines.utils import announce
from common.utils.s3 import TimestampedPrefix
import typing as t
from .configs import CloneIngestConfig, S3IngestConfig, LocalIngestConfig, CheckpointIngestConfig
from .steps import CloneIngestSteps
from pathlib import Path
import shutil

from time import sleep


@click.group(name='clone')
def clone_cli():
    """Clone Pipelines"""
    pass


@clone_cli.group(name='ingest')
@CloneIngestConfig.pass_options
@click.pass_context
def clone_ingest_cli(ctx: click.Context, **kwargs):
    """Clone Ingest Pipelines"""
    ctx.obj = CloneIngestConfig(**kwargs)


pass_clone_ingest_config = click.make_pass_decorator(CloneIngestConfig)


@clone_ingest_cli.command(name="s3")
@S3IngestConfig.pass_options
@pass_clone_ingest_config
def clone_s3_ingest(clone_ingest_config: CloneIngestConfig, **kwargs):
    """Pipeline for parsing docs directly from s3"""
    sig = S3IngestConfig.from_clone_config(
        clone_config=clone_ingest_config, other_config_kwargs=kwargs)
    announce("Aggregating files for processing ...")
    announce(
        f"Downloading raw files from s3 prefix: {sig.s3_raw_ingest_prefix} ...")
    sleep(5)

    Config.s3_utils.download_dir(
        local_dir=sig.raw_doc_base_dir,
        prefix_path=sig.s3_raw_ingest_prefix,
        bucket=sig.bucket_name
    )

#    if not next((p for p in sig.raw_doc_base_dir.iterdir() if p.is_file()), None):
#        announce("[WARNING] No files were downloaded for processing, exiting pipeline.")
#        exit(1)
    announce("Create metadata")
    CloneIngestSteps.create_metadata(sig)
    announce("Parse and OCR")
    CloneIngestSteps.parse_and_ocr(sig)
    CloneIngestSteps.load_files(sig)
    CloneIngestSteps.update_s3_cloning(sig)
    CloneIngestSteps.update_es(sig)

    announce("Pipeline Finished")


@clone_ingest_cli.command('reparse')
@pass_clone_ingest_config
def clone_reparse(clone_ingest_config: CloneIngestConfig, **kwargs):
    """Pipeline for pulling raw documents from s3, parsing, and reuploading/reindexing/populating neo4j"""
    announce('Pulling down raw snapshot files for parsing ...')
    clone_ingest_config.snapshot_manager.pull_current_snapshot_to_disk(
        local_dir=clone_ingest_config.raw_doc_base_dir,
        snapshot_type='raw',
        using_db=False,
        max_threads=clone_ingest_config.max_threads
    )

    if not next((p for p in clone_ingest_config.raw_doc_base_dir.iterdir() if p.is_file()), None):
        announce("[WARNING] No files were found for processing, exiting pipeline.")
        exit(1)
    CloneIngestSteps.backup_snapshots(clone_ingest_config)
    CloneIngestSteps.parse_and_ocr(clone_ingest_config)

    CloneIngestSteps.update_es(clone_ingest_config)

    # not available on clones yet
    # CloneIngestSteps.update_neo4j(clone_ingest_config)
    # CloneIngestSteps.update_revocations(clone_ingest_config)

    announce('Pushing up parsed files to s3 snapshot location ...')
    clone_ingest_config.snapshot_manager.update_current_snapshot_from_disk(
        local_dir=clone_ingest_config.parsed_doc_base_dir,
        snapshot_type='parsed',
        max_threads=clone_ingest_config.max_threads
    )


@clone_ingest_cli.command('reindex')
@pass_clone_ingest_config
def clone_reindex(clone_ingest_config: CloneIngestConfig, **kwargs):
    """Pipeline for pulling down jsons from s3 and reindexing into elasticsearch"""
    announce('Pulling down parsed snapshot files for reindexing ...')
    clone_ingest_config.snapshot_manager.pull_current_snapshot_to_disk(
        local_dir=clone_ingest_config.parsed_doc_base_dir,
        snapshot_type='parsed',
        using_db=False,
        max_threads=clone_ingest_config.max_threads
    )

    if not next((p for p in clone_ingest_config.parsed_doc_base_dir.iterdir() if p.is_file()), None):
        announce("[WARNING] No files were found for processing, exiting pipeline.")
        exit(1)

    announce('Reindexing in elasticsearch ...')
    CloneIngestSteps.update_es(clone_ingest_config)

    # not available on clones yet
    # CloneIngestSteps.update_revocations(clone_ingest_config)
