from common.document_parser.cli import pdf_to_json
from dataPipelines.gc_ingest.pipelines.utils import announce
from .configs import CoreIngestConfig, S3IngestConfig, DeleteConfig, ManifestConfig
from dataPipelines.gc_ingest.tools.snapshot.utils import SnapshotType
from datetime import datetime
from dataPipelines.gc_ingest.tools.load.cli import remove_docs_from_db
from dataPipelines.gc_ingest.tools.snapshot.cli import remove_docs_from_current_snapshot
from dataPipelines.gc_elasticsearch_publisher.cli import remove_docs_from_index
from dataPipelines.gc_neo4j_publisher.cli import remove_docs_from_neo4j
from dataPipelines.gc_ingest.tools.metadata.metadata import create_metadata_from_manifest


class PipelineSteps:
    pass


class CoreIngestSteps(PipelineSteps):

    @staticmethod
    def parse_and_ocr(c: CoreIngestConfig) -> None:
        announce(f"Parsing and OCR'ing docs from '{c.raw_doc_base_dir}' ...")
        pdf_to_json(
            parser_path="common.document_parser.parsers.policy_analytics.parse::parse",
            source=str(c.raw_doc_base_dir),
            destination=str(c.parsed_doc_base_dir),
            metadata=str(c.raw_doc_base_dir),
            ocr_missing_doc=True, 
            force_ocr=c.force_ocr,
            multiprocess=c.max_threads,
            num_ocr_threads=c.max_ocr_threads
        )

    @staticmethod
    def create_metadata(sc: S3IngestConfig) -> None:

        if sc.metadata_creation_group:
            announce("Creating metadata for files without existing metadata ...")
            sc.metadata_creater.create_metadata()

    @staticmethod
    def backup_db(c: CoreIngestConfig) -> None:
        if c.skip_db_backup:
            announce("Skipping DB backup ...")
        else:
            announce("Backing up DB(s) ...")
            c.core_db_manager.backup_all_tables_for_all_dbs(
                ts=c.batch_timestamp,
                job_dir=c.db_backup_dir
            )

    @staticmethod
    def load_files(c: CoreIngestConfig) -> None:
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
    def backup_snapshots(c: CoreIngestConfig) -> None:
        if not c.skip_snapshot_backup:
            announce("Backing up current snapshots ...")
            c.snapshot_manager.backup_all_current_snapshots(
                snapshot_ts=c.batch_timestamp
            )

    @staticmethod
    def update_s3_snapshots(c: CoreIngestConfig) -> None:
        announce("Updating raw/parsed snapshot locations in S3")
        c.snapshot_manager.update_current_snapshot_from_disk(
            local_dir=c.raw_doc_base_dir,
            snapshot_type=SnapshotType.RAW,
            replace=False,
            max_threads=c.max_s3_threads
        )
        c.snapshot_manager.update_current_snapshot_from_disk(
            local_dir=c.parsed_doc_base_dir,
            snapshot_type=SnapshotType.PARSED,
            replace=False,
            max_threads=c.max_s3_threads
        )
        c.snapshot_manager.update_current_snapshot_from_disk(
            local_dir=c.thumbnail_doc_base_dir,
            snapshot_type=SnapshotType.THUMBNAIL,
            replace=False,
            max_threads=c.max_s3_threads
        )

    @staticmethod
    def refresh_materialized_tables(c: CoreIngestConfig) -> None:
        announce("Refreshing materialized tables for all databases (e.g. web snapshot table) ...")
        c.core_db_manager.refresh_materialized_tables_for_all_dbs()

    @staticmethod
    def update_es(c: CoreIngestConfig) -> None:
        announce(f"Creating/Updating ES index: {c.index_name} ...")
        c.es_publisher.create_index()
        c.es_publisher.index_jsons()
        if c.alias_name:
            announce(f"Setting ES index('{c.index_name}') to alias('{c.alias_name}') ...")
            c.es_publisher.update_alias()

    @staticmethod
    def update_neo4j(c: CoreIngestConfig) -> None:
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
    def update_revocations(c: CoreIngestConfig) -> None:

        if c.skip_revocation_update:
            announce("Skipping Revocations update [flag set] ...")
            return

        announce("Updating revocations ...")
        c.crawler_status_tracker.handle_revocations(index_name=c.index_name,
            update_db=not c.skip_db_update,
            update_es=not c.skip_es_revocation,
            update_neo4j=False)

    @staticmethod
    def update_crawler_status_downloaded(c: CoreIngestConfig) -> None:

        if not c.crawler_output:
            announce("Skipping crawler_status table update [no crawler output file provided] ...")
            return

        announce("Updating crawler status table to Crawl and Download Complete...")
        c.crawler_status_tracker.update_crawler_status(status="Crawl and Download Complete",
                                                       timestamp=c.batch_timestamp,
                                                       update_db=not c.skip_db_update)

    @staticmethod
    def update_crawler_status_in_progress(c: CoreIngestConfig) -> None:

        if not c.crawler_output:
            announce("Skipping crawler_status table update [no crawler output file provided] ...")
            return

        announce("Updating crawler status table to In Progress...")
        c.crawler_status_tracker.update_crawler_status(status="Ingest In Progress",
                                                       timestamp=datetime.now(),
                                                       update_db=not c.skip_db_update)


    @staticmethod
    def update_crawler_status_completed(c: CoreIngestConfig) -> None:
        if not c.crawler_output:
            announce("Skipping crawler_status table update [no crawler output file provided] ...")
            return

        announce("Updating crawler status table to Ingest Complete...")
        c.crawler_status_tracker.update_crawler_status(status="Ingest Complete",
                                                       timestamp=datetime.now(),
                                                       update_db=not c.skip_db_update)

    @staticmethod
    def update_thumbnails(c: CoreIngestConfig) -> None:

        if c.skip_thumbnail_generation:
            announce("Skipping Thumbnails update [flag set] ...")
            return

        announce("Updating thumbnails ...")
        c.thumbnail_job_manager.process_directory()

    @staticmethod
    def delete_from_db(c: CoreIngestConfig) -> None:
        if c.skip_db_update:
            announce("Skip DB removal ...")
            return

        announce("Removing docs from DB ...")
        remove_docs_from_db(
            lm=c.load_manager,
            removal_list=c.db_tuple_list
        )

    @staticmethod
    def delete_from_s3(c: CoreIngestConfig) -> None:

        announce("Removing docs from S3 ...")
        remove_docs_from_current_snapshot(
            sm=c.snapshot_manager,
            removal_list=c.removal_list
        )

    @staticmethod
    def delete_from_elasticsearch(c: CoreIngestConfig) -> None:

        announce("Removing docs from Elasticsearch ...")

        remove_docs_from_index(index_name=c.index_name,
                               removal_list=c.removal_list)

    @staticmethod
    def delete_from_neo4j(c:CoreIngestConfig) -> None:

        if c.skip_neo4j_update:
            announce("Skip Neo4j removal ...")
            return
        announce("Removing docs from Neo4j ...")
        remove_docs_from_neo4j(
            njm=c.neo4j_job_manager,
            removal_list=c.removal_list
        )

    @staticmethod
    def create_metadata_from_manifest(mc: ManifestConfig) -> None:
        create_metadata_from_manifest(manifest_dict=mc.insert_manifest,
                                      output_dir=mc.raw_doc_base_dir)

