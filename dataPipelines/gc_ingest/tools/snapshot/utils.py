from pathlib import Path
import json
import sys
from common.utils.s3 import S3Utils
from common.utils.parsers import parse_timestamp
import typing as t
import datetime as dt
import shutil
from datetime import date
from dataPipelines.gc_ingest.config import Config
from dataPipelines.gc_db_utils.orch.models import SnapshotViewEntry
from dataPipelines.gc_db_utils.web.models import SnapshotEntry
from dataPipelines.gc_db_utils.web.schemas import SnapshotEntrySchema
from enum import Enum



class SnapshotType(Enum):
    RAW = 'raw'
    PARSED = 'parsed'
    THUMBNAIL = 'thumbnails'


class SnapshotManager:

    def __init__(self,
                 current_doc_snapshot_prefix: str,
                 backup_doc_snapshot_prefix: str,
                 bucket_name: str = Config.s3_bucket,
                 **ignored_kwargs):
        """Utils for managing raw/parsed data snapshots
        :param current_doc_snapshot_prefix: S3 prefix to where raw/parsed doc prefixes are located
        :param backup_doc_snapshot_prefix: S3 prefix to where backup raw/parsed doc prefixes are located
        :param bucket_name: S3 bucket name
        """
        self.s3u = S3Utils(ch=Config.connection_helper, bucket=Config.s3_bucket)
        self.bucket_name = bucket_name
        self.current_doc_snapshot_prefix = self.s3u.format_as_prefix(current_doc_snapshot_prefix)
        self.backup_doc_snapshot_prefix = self.s3u.format_as_prefix(backup_doc_snapshot_prefix)
        Config.connection_helper.init_dbs()
        self.shellu = shutil

    def get_current_prefix(self, snapshot_type: t.Union[SnapshotType, str]) -> str:
        """Get current prefix for the snapshot"""
        snapshot_type = SnapshotType(snapshot_type)
        return {
            SnapshotType.RAW: self.s3u.path_join(self.current_doc_snapshot_prefix, 'pdf/'),
            SnapshotType.PARSED: self.s3u.path_join(self.current_doc_snapshot_prefix, 'json/'),
            SnapshotType.THUMBNAIL: self.s3u.path_join(self.current_doc_snapshot_prefix, 'thumbnails/')
        }[snapshot_type]

    def get_backup_prefix(self, snapshot_type: t.Union[SnapshotType, str]) -> str:
        """Get backup prefix for the snapshot"""
        snapshot_type = SnapshotType(snapshot_type)
        return {
            SnapshotType.RAW: self.s3u.path_join(self.backup_doc_snapshot_prefix, 'pdf/'),
            SnapshotType.PARSED: self.s3u.path_join(self.backup_doc_snapshot_prefix, 'json/'),
            SnapshotType.THUMBNAIL: self.s3u.path_join(self.backup_doc_snapshot_prefix, 'thumbnails/')
        }[snapshot_type]

    def get_backup_prefix_for_ts(self, snapshot_type: t.Union[SnapshotType, str], ts: t.Union[dt.datetime, str]) -> str:
        """Get timestamped backup prefix for the snapshot"""
        snapshot_type = SnapshotType(snapshot_type)
        return self.s3u.get_prefix_at_ts(
            base_prefix=self.get_backup_prefix(snapshot_type),
            ts=ts,
            ts_fmt=Config.TIMESTAMP_FORMAT
        )

    def get_orch_db_snapshot_entries(self, scroll_window: int = 1000) -> t.Iterable['SnapshotViewEntry']:
        """Iterate through all snapshot entries
        :param scroll_window: How many entries to fetch from db at any given time
        :return: Iterable of snapshot entries
        """
        ch = Config.connection_helper

        with ch.orch_db_session_scope('ro') as session:
            for obj in session.query(SnapshotViewEntry).yield_per(scroll_window):
                yield obj

    def recreate_web_db_snapshot(self) -> None:
        """Recreate snapshot table in web db using snapshot view from orch db"""

        def truncate_web_db_snapshot() -> None:
            """Trims the snapshot table"""
            ch = Config.connection_helper

            with ch.web_db_session_scope('rw') as session:
                session.execute(f'TRUNCATE TABLE {SnapshotEntry.__tablename__}')

        with Config.connection_helper.web_db_session_scope('rw') as session:
            web_db_entries = [
                SnapshotEntry(**{k: getattr(orch_entry, k) for k, _ in SnapshotEntrySchema.__dict__.items() if
                                 not k.startswith('_')})
                for orch_entry in self.get_orch_db_snapshot_entries()
            ]

            if not web_db_entries:
                return

            truncate_web_db_snapshot()
            session.add_all(web_db_entries)

    def pull_current_snapshot_to_disk(self,
                                      local_dir: t.Union[Path, str],
                                      snapshot_type: t.Union[SnapshotType, str],
                                      using_db: bool = True,
                                      max_threads: int = -1) -> None:
        """Pull files for the most current raw/parsed snapshot to disk.
        :param local_dir: Path to local directory where the snapshot files should be downloaded
        :param snapshot_type: raw/parsed type of snapshot to pull
        :param using_db: Whether to use orchestration db to figure out what docs belong to a snapshot
            or just pull from current snapshot s3 location
        :param max_threads: maximum number of threads for multithreading
        :return: None - downloads files into <local_dir> as a side-effect
        """
        local_dir = Path(local_dir).resolve()
        local_dir.mkdir(exist_ok=True)
        snapshot_type = SnapshotType(snapshot_type)
        current_prefix = self.get_current_prefix(snapshot_type)

        print(f"Downloading snapshot to local dir: {local_dir!s}", file=sys.stderr)
        if using_db and snapshot_type == SnapshotType.RAW:
            for snapshot_entry in self.get_orch_db_snapshot_entries():
                print(f"Downloading f{snapshot_entry.doc_s3_location} to local dir & writing metadata ... ",
                      file=sys.stderr)
                self.s3u.download_file(
                    object_path=snapshot_entry.doc_s3_location,
                    file=Path(local_dir, Path(snapshot_entry.doc_s3_location).name)
                )
                with Path(local_dir, Path(snapshot_entry.doc_s3_location).name + ".metadata").open("w") as f:
                    f.write(snapshot_entry.json_metadata)

        else:
            print(f"Downloading all files from snapshot at {current_prefix} to local dir {local_dir!s} ...",
                  file=sys.stderr)
            self.s3u.download_dir(
                local_dir=local_dir,
                prefix_path=current_prefix,
                max_threads=max_threads
            )

    def zip_folder_and_upload_to_s3(self, local_dir: t.Union[Path, str],
                                    snapshot_type: t.Union[SnapshotType, str],
                                    max_threads) -> None:
        """zip json files and upload to s3
        :param local_dir: path to local flat directory with the files
        :param snapshot_type: type of snapshot raw/parsed
        :param max_threads: maximum number of threads for multiprocessing
        """
        local_dir = Path(local_dir).resolve()
        prefix = self.get_current_prefix(snapshot_type)
        print("dir" + str(local_dir))
        self.shellu.make_archive('./json_files', 'zip', local_dir)
        self.s3u.upload_file(file='./json_files' + '.zip', object_prefix=prefix)

    # TODO: avoid deleting all files first to avoid app downtime
    def update_current_snapshot_from_disk(self, local_dir: t.Union[Path, str],
                                          snapshot_type: t.Union[SnapshotType, str],
                                          replace: bool = False,
                                          max_threads: int = -1) -> None:
        """Update current raw/parsed snapshot
        :param local_dir: path to local flat directory with the files
        :param snapshot_type: type of snapshot raw/parsed
        :param replace: whether to delete all destination files first
        :param max_threads: maximum number of threads for multiprocessing
        """
        local_dir = Path(local_dir).resolve()
        snapshot_type = SnapshotType(snapshot_type)
        prefix = self.get_current_prefix(snapshot_type)

        if replace:
            print(f"Deleting current snapshot files before processing update ...", file=sys.stderr)
            self.s3u.delete_prefix(prefix=prefix, max_threads=max_threads)

        print(f"Updating current snapshot at {prefix} prefix with contents of local dir {local_dir!s} ... ",
              file=sys.stderr)
        self.s3u.upload_dir(local_dir=local_dir, prefix_path=prefix, max_threads=max_threads)

    def backup_current_snapshot(self,
                                snapshot_type: t.Union[SnapshotType, str],
                                snapshot_ts: t.Union[dt.datetime, str] = dt.datetime.now()) -> t.Optional[str]:
        """Backup current raw/parsed snapshot to timestamped location in S3
        :param snapshot_type: type of snapshot - raw/parsed
        :param snapshot_ts: timestamp to use when constructing the backup prefix
        :return: s3 prefix to the backup
        """
        snapshot_type = SnapshotType(snapshot_type)
        snapshot_ts = parse_timestamp(snapshot_ts, raise_parse_error=True)
        current_prefix = self.get_current_prefix(snapshot_type)
        backup_prefix = self.get_backup_prefix_for_ts(snapshot_type=snapshot_type, ts=snapshot_ts)

        if self.s3u.prefix_exists(backup_prefix):
            raise ValueError(
                f"Cannot backup current snapshot because corresponding prefix already exists: {backup_prefix}")
        if not self.s3u.prefix_exists(current_prefix):
            print(f"Cannot backup current snapshot because there's nothing there: {current_prefix}", file=sys.stderr)
            return None

        print(f"Backing up current prefix {current_prefix} to archive {backup_prefix} ...", file=sys.stderr)
        self.s3u.copy_prefix(
            src_prefix=current_prefix,
            dst_prefix=backup_prefix
        )
        return backup_prefix

    def backup_all_current_snapshots(self, snapshot_ts: t.Union[dt.datetime, str] = dt.datetime.now()) -> t.List[str]:
        """Backup snapshots for all databases"""
        snapshot_ts = parse_timestamp(ts=snapshot_ts, raise_parse_error=True)
        backed_up_snapshot_paths: t.List[str] = []
        for st in SnapshotType:
            s3_path = self.backup_current_snapshot(
                snapshot_type=st,
                snapshot_ts=snapshot_ts
            )
            if s3_path:
                backed_up_snapshot_paths.append(s3_path)
        return backed_up_snapshot_paths

    def restore_current_snapshot(self,
                                 snapshot_type: t.Union[SnapshotType, str],
                                 snapshot_ts: t.Union[dt.datetime, str]) -> str:
        """Restore current raw/parsed snapshot from one corresponding to a timestamp
        :param snapshot_type: type of snapshot - raw/parsed
        :param snapshot_tis: timestamp to use when figuring out what prefix to restore from
        :return: s3 prefix to the current snapshot
        """
        snapshot_type = SnapshotType(snapshot_type)
        snapshot_ts = parse_timestamp(snapshot_ts)
        current_prefix = self.get_current_prefix(snapshot_type)
        backup_prefix = self.get_backup_prefix_for_ts(snapshot_type=snapshot_type, ts=snapshot_ts)

        if not self.s3u.prefix_exists(backup_prefix):
            raise ValueError(f"Cannot restore backup prefix, it doesn't exist: {backup_prefix}")
        if self.s3u.prefix_exists(current_prefix):
            print(f"Deleting current prefix prior to restore: {current_prefix} ...", file=sys.stderr)
            for obj_path in self.s3u.iter_object_paths_at_prefix(current_prefix):
                self.s3u.delete_object(obj_path)

        print(f"Restoring current prefix - {current_prefix} - from backup at {backup_prefix} ...", file=sys.stderr)
        self.s3u.copy_prefix(
            src_prefix=backup_prefix,
            dst_prefix=current_prefix
        )
        return current_prefix

    def restore_all_current_snapshots(self, snapshot_ts: t.Union[dt.datetime, str] = dt.datetime.now()) -> t.List[str]:
        """Restore current snapshots for all databases"""
        snapshot_ts = parse_timestamp(ts=snapshot_ts, raise_parse_error=True)
        restored_current_prefixes: t.List[str] = []
        for st in SnapshotType:
            s3_path = self.restore_current_snapshot(
                snapshot_type=st,
                snapshot_ts=snapshot_ts
            )
            restored_current_prefixes.append(s3_path)
        return restored_current_prefixes

    def delete_from_current_snapshot(self, filename: t.Union[str, Path]):

        raw_path = self.s3u.path_join(self.get_current_prefix( SnapshotType.RAW),
                                        filename.name)
        print(f"Deleting {raw_path!s} from S3 bucket {self.bucket_name!s} ... ", file=sys.stderr)
        self.s3u.delete_object(object_path=raw_path, bucket=self.bucket_name)

        # Delete metdata file from s3
        metadata_filename = Path(filename.name+".metadata")
        metadata_path = self.s3u.path_join(self.get_current_prefix(SnapshotType.RAW),
                                            metadata_filename.name)
        print(f"Deleting {metadata_path!s} from S3 bucket {self.bucket_name!s} ... ", file=sys.stderr)
        self.s3u.delete_object(object_path=metadata_path, bucket=self.bucket_name)

        # Delete parsed file from s3
        parsed_filename = Path(filename.stem + ".json")
        parsed_path = self.s3u.path_join(self.get_current_prefix(SnapshotType.PARSED),
                                         parsed_filename.name)
        print(f"Deleting {parsed_path!s} from S3 bucket {self.bucket_name!s} ... ", file=sys.stderr)
        self.s3u.delete_object(object_path=parsed_path, bucket=self.bucket_name)

        # Delete thumbnail file from s3
        thumbnail_filename = Path(filename.stem + ".png")
        thumbnail_path = self.s3u.path_join(self.get_current_prefix(SnapshotType.THUMBNAIL),
                                            thumbnail_filename.name)
        print(f"Deleting {thumbnail_path!s} from S3 bucket {self.bucket_name!s} ... ", file=sys.stderr)
        self.s3u.delete_object(object_path=thumbnail_path, bucket=self.bucket_name)