import click
from dataPipelines.gc_ingest.config import Config
from dataPipelines.gc_ingest.pipelines.utils import announce
from common.utils.s3 import TimestampedPrefix
import typing as t
from .configs import CoreIngestConfig, S3IngestConfig, LocalIngestConfig, CheckpointIngestConfig, DeleteConfig, ManifestConfig
from .steps import CoreIngestSteps
from pathlib import Path
import shutil
import glob


@click.group(name='core')
def core_cli():
    """Core Pipelines"""
    pass


@core_cli.group(name='ingest')
@CoreIngestConfig.pass_options
@click.pass_context
def core_ingest_cli(ctx: click.Context, **kwargs):
    """Core Ingest Pipelines"""
    ctx.obj = CoreIngestConfig(**kwargs)


pass_core_ingest_config = click.make_pass_decorator(CoreIngestConfig)


@core_ingest_cli.command(name="s3")
@S3IngestConfig.pass_options
@pass_core_ingest_config
def core_s3_ingest(core_ingest_config: CoreIngestConfig, **kwargs):
    """Pipeline for parsing docs directly from s3"""
    sig = S3IngestConfig.from_core_config(core_config=core_ingest_config, other_config_kwargs=kwargs)

    announce("Aggregating files for processing ...")
    announce(f"Downloading raw files from s3 prefix: {sig.s3_raw_ingest_prefix} ...")
    Config.s3_utils.download_dir(
        local_dir=sig.raw_doc_base_dir,
        prefix_path=sig.s3_raw_ingest_prefix,
        bucket=sig.bucket_name
    )

    if not next((p for p in sig.raw_doc_base_dir.iterdir() if p.is_file()), None):
        announce("[WARNING] No files were downloaded for processing, exiting pipeline.")
        exit(1)

    CoreIngestSteps.create_metadata(sig)

    CoreIngestSteps.backup_db(sig)
    CoreIngestSteps.backup_snapshots(sig)

    if sig.s3_parsed_ingest_prefix:
        announce(f"Downloading parsed files from s3 prefix: {sig.s3_parsed_ingest_prefix} ...")
        Config.s3_utils.download_dir(
            local_dir=sig.parsed_doc_base_dir,
            prefix_path=sig.s3_parsed_ingest_prefix,
            bucket=sig.bucket_name
        )
        if not next((p for p in sig.parsed_doc_base_dir.iterdir() if p.is_file()), None):
            announce("[WARNING] No parsed files were downloaded for processing, exiting pipeline.")
            exit(1)
    else:
        CoreIngestSteps.parse_and_ocr(sig)

    CoreIngestSteps.update_thumbnails(sig)
    CoreIngestSteps.load_files(sig)
    CoreIngestSteps.update_s3_snapshots(sig)
    CoreIngestSteps.refresh_materialized_tables(sig)
    CoreIngestSteps.update_es(sig)
    CoreIngestSteps.update_neo4j(sig)

    announce("Pipeline Finished")


@core_ingest_cli.command(name="checkpoint")
@CheckpointIngestConfig.pass_options
@pass_core_ingest_config
def core_checkpoint_ingest(core_ingest_config: CoreIngestConfig, **kwargs):
    """Pipeline for parsing focs from checkpointed s3 prefixes"""
    cig = CheckpointIngestConfig.from_core_config(core_config=core_ingest_config, other_config_kwargs=kwargs)

    announce("Aggregating files for processing ...")
    announce(f"Aggregating files from checkpoints ...")
    last_prefix: t.Optional[TimestampedPrefix] = None
    with cig.checkpoint_manager.checkpoint_download_manager(
        base_download_dir=cig.download_base_dir,
        advance_checkpoint=cig.advance_checkpoint,
        limit=cig.checkpoint_limit if cig.checkpoint_limit > 0 else None,
        max_threads=cig.max_threads
    ) as downloaded_prefixes:
        for dp in downloaded_prefixes:
            last_prefix = dp.timestamped_prefix
            for f in (p for p in dp.local_path.iterdir() if p.is_file()):
                shutil.copy(str(f), str(Path(cig.raw_doc_base_dir, f.name)))

    if not last_prefix:
        announce("There was nothing to do, skipping remainder of ingest ...")
        exit(0)

    if not next((p for p in cig.raw_doc_base_dir.iterdir() if p.is_file()), None):
        announce("[WARNING] No files were downloaded for processing, exiting pipeline.")
        exit(1)

    CoreIngestSteps.update_crawler_status_downloaded(cig)
    CoreIngestSteps.update_crawler_status_in_progress(cig)
    CoreIngestSteps.backup_db(cig)
    CoreIngestSteps.backup_snapshots(cig)
    CoreIngestSteps.update_thumbnails(cig)
    CoreIngestSteps.parse_and_ocr(cig)
    CoreIngestSteps.load_files(cig)
    CoreIngestSteps.update_s3_snapshots(cig)
    CoreIngestSteps.refresh_materialized_tables(cig)
    CoreIngestSteps.update_es(cig)
    CoreIngestSteps.update_neo4j(cig)
    CoreIngestSteps.update_revocations(cig)
    CoreIngestSteps.update_crawler_status_completed(cig)

    announce("Pipeline Finished")


@core_ingest_cli.command('local')
@LocalIngestConfig.pass_options
@pass_core_ingest_config
def core_local_ingest(core_ingest_config: CoreIngestConfig, **kwargs):
    """Pipeline for ingesting docs from local directories"""
    lic = LocalIngestConfig.from_core_config(core_config=core_ingest_config, other_config_kwargs=kwargs)

    if not next((p for p in lic.raw_doc_base_dir.iterdir() if p.is_file()), None):
        announce("[WARNING] No files were found for processing, exiting pipeline.")
        exit(1)
    CoreIngestSteps.update_crawler_status_downloaded(lic)
    CoreIngestSteps.update_crawler_status_in_progress(lic)
    CoreIngestSteps.backup_db(lic)
    CoreIngestSteps.backup_snapshots(lic)
    CoreIngestSteps.update_thumbnails(lic)
    if not lic.skip_parse:
        announce("Parsed files passed, skipping parsing.")
        CoreIngestSteps.parse_and_ocr(lic)
    CoreIngestSteps.load_files(lic)
    CoreIngestSteps.update_s3_snapshots(lic)
    CoreIngestSteps.refresh_materialized_tables(lic)
    CoreIngestSteps.update_es(lic)
    CoreIngestSteps.update_neo4j(lic)
    CoreIngestSteps.update_revocations(lic)
    CoreIngestSteps.update_crawler_status_completed(lic)

    announce("Pipeline Finished")


@core_ingest_cli.command('reparse')
@pass_core_ingest_config
def core_reparse(core_ingest_config: CoreIngestConfig, **kwargs):
    """Pipeline for pulling raw documents from s3, parsing, and reuploading/reindexing/populating neo4j"""
    announce('Pulling down raw snapshot files for parsing ...')
    core_ingest_config.snapshot_manager.pull_current_snapshot_to_disk(
        local_dir=core_ingest_config.raw_doc_base_dir,
        snapshot_type='raw',
        using_db=False,
        max_threads=core_ingest_config.max_threads
    )

    if not next((p for p in core_ingest_config.raw_doc_base_dir.iterdir() if p.is_file()), None):
        announce("[WARNING] No files were found for processing, exiting pipeline.")
        exit(1)
    CoreIngestSteps.backup_snapshots(core_ingest_config)
    CoreIngestSteps.update_thumbnails(core_ingest_config)
    CoreIngestSteps.parse_and_ocr(core_ingest_config)

    CoreIngestSteps.update_es(core_ingest_config)
    CoreIngestSteps.update_neo4j(core_ingest_config)
    CoreIngestSteps.update_revocations(core_ingest_config)

    announce('Pushing up parsed files to s3 snapshot location ...')
    core_ingest_config.snapshot_manager.update_current_snapshot_from_disk(
        local_dir=core_ingest_config.parsed_doc_base_dir,
        snapshot_type='parsed',
        max_threads=core_ingest_config.max_threads
    )

    if core_ingest_config.force_ocr:
        announce('Pushing up raw files to s3 snapshot location ...')
        core_ingest_config.snapshot_manager.update_current_snapshot_from_disk(
            local_dir=core_ingest_config.raw_doc_base_dir,
            snapshot_type='raw',
            max_threads=core_ingest_config.max_threads
        )

    if not core_ingest_config.skip_thumbnail_generation:
        announce('Pushing up thumbnails to s3 snapshot location ...')
        core_ingest_config.snapshot_manager.update_current_snapshot_from_disk(
            local_dir=core_ingest_config.thumbnail_doc_base_dir,
            snapshot_type='thumbnails',
            max_threads=core_ingest_config.max_threads
        )


@core_ingest_cli.command('reindex')
@pass_core_ingest_config
def core_reindex(core_ingest_config: CoreIngestConfig, **kwargs):
    """Pipeline for pulling down jsons from s3 and reindexing into elasticsearch"""
    announce('Pulling down parsed snapshot files for reindexing ...')
    core_ingest_config.snapshot_manager.pull_current_snapshot_to_disk(
        local_dir=core_ingest_config.parsed_doc_base_dir,
        snapshot_type='parsed',
        using_db=False,
        max_threads=core_ingest_config.max_threads
    )

    if not next((p for p in core_ingest_config.parsed_doc_base_dir.iterdir() if p.is_file()), None):
        announce("[WARNING] No files were found for processing, exiting pipeline.")
        exit(1)

    announce('Reindexing in elasticsearch ...')
    CoreIngestSteps.update_es(core_ingest_config)
    CoreIngestSteps.update_revocations(core_ingest_config)


@core_ingest_cli.command('update-neo4j')
@pass_core_ingest_config
def core_update_neo4j(core_ingest_config: CoreIngestConfig, **kwargs):
    """Pipeline for pulling down jsons from s3 and repopulating neo4j"""
    announce('Pulling down parsed snapshot files for updating neo4j ...')
    core_ingest_config.snapshot_manager.pull_current_snapshot_to_disk(
        local_dir=core_ingest_config.parsed_doc_base_dir,
        snapshot_type='parsed',
        using_db=False,
        max_threads=core_ingest_config.max_threads
    )

    if not next((p for p in core_ingest_config.parsed_doc_base_dir.iterdir() if p.is_file()), None):
        announce("[WARNING] No files were found for processing, exiting pipeline.")
        exit(1)

    announce('Updating neo4j ...')
    CoreIngestSteps.update_neo4j(core_ingest_config)

    
@core_ingest_cli.command('update-thumbnails')
@pass_core_ingest_config
def core_update_thumbnails(core_ingest_config: CoreIngestConfig, **kwargs):
    """Pipeline for pulling down pdfs/metadata from s3 and updating thumbnails"""
    announce('Pulling down parsed snapshot files for updating neo4j ...')
    core_ingest_config.snapshot_manager.pull_current_snapshot_to_disk(
        local_dir=core_ingest_config.raw_doc_base_dir,
        snapshot_type='raw',
        using_db=False,
        max_threads=core_ingest_config.max_threads
    )

    if not next((p for p in core_ingest_config.raw_doc_base_dir.iterdir() if p.is_file()), None):
        announce("[WARNING] No files were found for processing, exiting pipeline.")
        exit(1)

    announce('Updating thumbnails ...')
    CoreIngestSteps.update_thumbnails(core_ingest_config)

    announce('Pushing up thumbnails to s3 snapshot location ...')
    core_ingest_config.snapshot_manager.update_current_snapshot_from_disk(
        local_dir=core_ingest_config.thumbnail_doc_base_dir,
        snapshot_type='thumbnails',
        max_threads=core_ingest_config.max_threads
    )


@core_ingest_cli.command('delete')
@pass_core_ingest_config
@DeleteConfig.pass_options
def core_delete(core_ingest_config: CoreIngestConfig, **kwargs):
    """Pipeline for ingesting docs from local directories"""
    dc = DeleteConfig.from_core_config(core_config=core_ingest_config, other_config_kwargs=kwargs)

    CoreIngestSteps.backup_db(dc)
    CoreIngestSteps.backup_snapshots(dc)

    CoreIngestSteps.delete_from_elasticsearch(dc)

    CoreIngestSteps.delete_from_neo4j(dc)

    CoreIngestSteps.delete_from_db(dc)
    CoreIngestSteps.refresh_materialized_tables(dc)

    CoreIngestSteps.delete_from_s3(dc)

@core_ingest_cli.command('manifest')
@pass_core_ingest_config
@ManifestConfig.pass_options
def core_manifest(core_ingest_config: CoreIngestConfig, **kwargs):
    """Pipeline for ingesting docs from local directories"""
    mc = ManifestConfig.from_core_config(core_config=core_ingest_config, other_config_kwargs=kwargs)

    # Setup Steps
    announce("Aggregating files for processing ...")
    announce(f"Downloading raw files from s3 prefix: {mc.s3_raw_ingest_prefix} ...")
    Config.s3_utils.download_dir(
        local_dir=mc.raw_doc_base_dir,
        prefix_path=mc.s3_raw_ingest_prefix,
        bucket=mc.bucket_name
    )

    CoreIngestSteps.backup_db(mc)
    CoreIngestSteps.backup_snapshots(mc)
    count_docs_copied = len(glob.glob(str(mc.raw_doc_base_dir) +"/*.*"))
    if count_docs_copied == 0:
        announce("[WARNING] No files were downloaded for processing, exiting pipeline.")
        exit(1)
    elif count_docs_copied > 1:
        # Ingest Steps -- Skipped if no files to ingest
        CoreIngestSteps.create_metadata_from_manifest(mc)
        CoreIngestSteps.parse_and_ocr(mc)

        CoreIngestSteps.update_thumbnails(mc)
        CoreIngestSteps.load_files(mc)
        CoreIngestSteps.update_s3_snapshots(mc)
        CoreIngestSteps.refresh_materialized_tables(mc)
        CoreIngestSteps.update_es(mc)
        CoreIngestSteps.update_neo4j(mc)

    # Delete Steps
    CoreIngestSteps.delete_from_elasticsearch(mc)

    CoreIngestSteps.delete_from_neo4j(mc)

    CoreIngestSteps.delete_from_db(mc)
    CoreIngestSteps.refresh_materialized_tables(mc)

    CoreIngestSteps.delete_from_s3(mc)
