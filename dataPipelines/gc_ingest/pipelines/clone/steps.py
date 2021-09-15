from common.document_parser.cli import pdf_to_json
from dataPipelines.gc_ingest.pipelines.utils import announce
from .configs import CloneIngestConfig, S3IngestConfig
from dataPipelines.gc_ingest.tools.snapshot.utils import SnapshotType
from datetime import datetime

class PipelineSteps:
    pass


class CloneIngestSteps(PipelineSteps):

    @staticmethod
    def parse_and_ocr(c: CloneIngestConfig) -> None:
        announce(f"Parsing and OCR'ing docs from '{c.raw_doc_base_dir}' ...")
        pdf_to_json(
            parser_path="common.document_parser.parsers.policy_analytics.parse::parse",
            source=str(c.raw_doc_base_dir),
            destination=str(c.parsed_doc_base_dir),
            metadata=str(c.raw_doc_base_dir),
            ocr_missing_doc=True,
            multiprocess=c.max_threads,
            num_ocr_threads=c.max_ocr_threads
        )

    @staticmethod
    def create_metadata(sc: S3IngestConfig) -> None:

        if sc.metadata_creation_group:
            announce("Creating metadata for files without existing metadata ...")
            sc.metadata_creater.create_metadata()

    @staticmethod
    def backup_db(c: CloneIngestConfig) -> None:
        if c.skip_db_backup:
            announce("Skipping DB backup ...")
        else:
            announce("Backing up DB(s) ...")
            c.clone_db_manager.backup_all_tables_for_all_dbs(
                ts=c.batch_timestamp,
                job_dir=c.db_backup_dir
            )

    @staticmethod
    def load_files(c: CloneIngestConfig) -> None:
        announce("Loading files into S3 & DB ...")
        c.load_manager.load(
            raw_dir=c.raw_doc_base_dir,
            metadata_dir=c.raw_doc_base_dir,
            parsed_dir=c.parsed_doc_base_dir,
            ingest_ts=c.batch_timestamp,
            update_s3=True,
            max_threads=c.max_s3_threads,
            update_db=not c.skip_db_update,
            thumbnail_dir=c.thumbnail_doc_base_dir
        )

    @staticmethod
    def backup_snapshots(c: CloneIngestConfig) -> None:
        if not c.skip_snapshot_backup:
            announce("Backing up current snapshots ...")
            c.snapshot_manager.backup_all_current_snapshots(
                snapshot_ts=c.batch_timestamp
            )
            
    @staticmethod
    def update_s3_cloning(c: CloneIngestConfig) -> None:
        announce("Updating raw/parsed snapshot locations in S3")
        c.snapshot_manager.update_current_snapshot_from_disk(
            local_dir=c.raw_doc_base_dir,
            snapshot_type=SnapshotType.RAW,
            replace=False,
            max_threads=c.max_threads
        )
        c.snapshot_manager.update_current_snapshot_from_disk(
            local_dir=c.parsed_doc_base_dir,
            snapshot_type=SnapshotType.PARSED,
            replace=False,
            max_threads=c.max_threads
        )
        c.snapshot_manager.update_current_snapshot_from_disk(
            local_dir=c.thumbnail_doc_base_dir,
            snapshot_type=SnapshotType.THUMBNAIL,
            replace=False,
            max_threads=c.max_threads
        )

    @staticmethod
    def update_s3_snapshots(c: CloneIngestConfig) -> None:
        announce("Updating raw/parsed snapshot locations in S3")
        c.snapshot_manager.update_current_snapshot_from_disk(
            local_dir=c.raw_doc_base_dir,
            snapshot_type=SnapshotType.RAW,
            replace=False,
            max_threads=c.max_threads
        )
        c.snapshot_manager.update_current_snapshot_from_disk(
            local_dir=c.parsed_doc_base_dir,
            snapshot_type=SnapshotType.PARSED,
            replace=False,
            max_threads=c.max_threads
        )
        c.snapshot_manager.update_current_snapshot_from_disk(
            local_dir=c.thumbnail_doc_base_dir,
            snapshot_type=SnapshotType.THUMBNAIL,
            replace=False,
            max_threads=c.max_threads
        )

    @staticmethod
    def refresh_materialized_tables(c: CloneIngestConfig) -> None:
        announce("Refreshing materialized tables for all databases (e.g. web snapshot table) ...")
        c.clone_db_manager.refresh_materialized_tables_for_all_dbs()

    @staticmethod
    def update_es(c: CloneIngestConfig) -> None:
        announce(f"Creating/Updating ES index: {c.index_name} ...")
        c.es_publisher.create_index()
        c.es_publisher.index_jsons()
        if c.alias_name:
            announce(f"Setting ES index('{c.index_name}') to alias('{c.alias_name}') ...")
            c.es_publisher.update_alias()

    @staticmethod
    def update_neo4j(c: CloneIngestConfig) -> None:
        if c.skip_neo4j_update:
            announce("Skipping Neo4J update ...")
        else:
            announce("Updating Neo4J ...")
            c.neo4j_job_manager.run_update(
                source=c.parsed_doc_base_dir,
                clear=False,
                max_threads=c.max_threads_neo4j,
                scrape_wiki=False,
                without_web_scraping=True,
                infobox_dir=c.infobox_dir
            )

    @staticmethod
    def update_revocations(c: CloneIngestConfig) -> None:

        if c.skip_revocation_update:
            announce("Skipping Revocations update [flag set] ...")
            return

        announce("Updating revocations ...")
        c.crawler_status_tracker.handle_revocations(index_name=c.index_name,
            update_db=not c.skip_db_update,
            update_es=not c.skip_es_revocation,
            update_neo4j=not c.skip_neo4j_update)

    @staticmethod
    def update_crawler_status_downloaded(c: CloneIngestConfig) -> None:

        if not c.crawler_output:
            announce("Skipping crawler_status table update [no crawler output file provided] ...")
            return

        announce("Updating crawler status table to Crawl and Download Complete...")
        c.crawler_status_tracker.update_crawler_status(status="Crawl and Download Complete",
                                                       timestamp=c.batch_timestamp,
                                                       update_db=not c.skip_db_update)

    @staticmethod
    def update_crawler_status_in_progress(c: CloneIngestConfig) -> None:

        if not c.crawler_output:
            announce("Skipping crawler_status table update [no crawler output file provided] ...")
            return

        announce("Updating crawler status table to In Progress...")
        c.crawler_status_tracker.update_crawler_status(status="Ingest In Progress",
                                                       timestamp=datetime.now(),
                                                       update_db=not c.skip_db_update)


    @staticmethod
    def update_crawler_status_completed(c: CloneIngestConfig) -> None:
        if not c.crawler_output:
            announce("Skipping crawler_status table update [no crawler output file provided] ...")
            return

        announce("Updating crawler status table to Ingest Complete...")
        c.crawler_status_tracker.update_crawler_status(status="Ingest Complete",
                                                       timestamp=datetime.now(),
                                                       update_db=not c.skip_db_update)


    @staticmethod
    def update_thumbnails(c: CloneIngestConfig) -> None:

        if c.skip_thumbnail_generation:
            announce("Skipping Thumbnails update [flag set] ...")
            return

        announce("Updating thumbnails ...")
        c.thumbnail_job_manager.process_directory()
