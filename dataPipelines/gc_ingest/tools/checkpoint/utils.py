from common.utils.s3 import TimestampedPrefix, S3Utils
from dataPipelines.gc_ingest.config import Config
from contextlib import contextmanager
from pathlib import Path
import datetime as dt
import typing as t


class DownloadedPrefix(t.NamedTuple):
    """Timestamped prefix downloaded to a local directory"""
    local_path: Path
    timestamped_prefix: TimestampedPrefix


class CheckpointManager:
    def __init__(self,
                 checkpoint_file_path: str,
                 checkpointed_dir_path: str,
                 bucket_name: str = Config.s3_bucket,
                 checkpoint_ready_marker: t.Optional[str] = None,
                 **ignored_kwargs):
        """Utility class for dealing with checkpointed paths in S3
        :param checkpoint_file_path: Path to checkpoint file in s3 (sans bucket name)
        :param checkpointed_dir_path: Path to checkpointed base path in s3 (sans bucket name)
        :param bucket_name: S3 Bucket name
        :param ready_marker: Name of the file that marks checkpointed directory as ready for processing
        """
        self.checkpoint_file_path = checkpoint_file_path
        self.checkpointed_dir_path = (
            checkpointed_dir_path if checkpointed_dir_path.endswith('/')
            else checkpointed_dir_path + '/'
        )
        self.bucket_name = bucket_name
        self.s3u = S3Utils(Config.connection_helper, bucket=self.bucket_name)
        self.ready_marker = checkpoint_ready_marker


    @property
    def current_checkpoint_ts(self) -> t.Optional[dt.datetime]:
        return self.s3u.get_checkpoint_ts(self.checkpoint_file_path)

    @current_checkpoint_ts.setter
    def current_checkpoint_ts(self, new_value: t.Union[dt.datetime, str]) -> None:

        self.s3u.update_checkpoint(
            timestamp=new_value,
            checkpoint_path=self.checkpoint_file_path
        )

    @current_checkpoint_ts.deleter
    def current_checkpoint_ts(self) -> None:
        self.s3u.delete_object(self.checkpoint_file_path)
        self.current_checkpoint_ts = self.current_checkpoint_ts

    @property
    def current_prefix(self) -> t.Optional[TimestampedPrefix]:
        ts = self.current_checkpoint_ts
        if ts:
            ts_str = ts.strftime(S3Utils.TIMESTAMP_FORMAT)
            return TimestampedPrefix(
                prefix_path=self.checkpointed_dir_path + ts_str,
                timestamp=ts,
                timestamp_str=ts_str
            )
        else:
            return None

    @current_prefix.setter
    def current_prefix(self, new_value: TimestampedPrefix) -> None:
        self.current_checkpoint_ts = new_value.timestamp

    @current_prefix.deleter
    def current_prefix(self):
        del self.current_checkpoint_ts
        self.current_prefix = self.current_prefix

    def is_prefix_ready_for_processing(self, prefix: t.Union[TimestampedPrefix, str]) -> bool:
        if not self.ready_marker:
            return True
        else:
            return self.s3u.object_exists(
                self.s3u.format_as_prefix(prefix.prefix_path if isinstance(prefix, TimestampedPrefix) else prefix)
                + self.ready_marker
            )

    @property
    def all_prefixes(self) -> t.List[TimestampedPrefix]:
        return [
            tp for tp in
            self.s3u.get_timestamped_prefixes(
                base_prefix=self.checkpointed_dir_path
            )
            if self.is_prefix_ready_for_processing(tp)
        ]

    @all_prefixes.setter
    def all_prefixes(self, new_value: t.Iterable[TimestampedPrefix]) -> None:
        raise NotImplemented("Unable to set all prefixes - not implemented or meant to be used this way.")

    @all_prefixes.deleter
    def all_prefixes(self) -> None:
        raise NotImplemented("Unable to delete all prefixes. Remove them in the storage")

    @property
    def remaining_prefixes(self) -> t.List[TimestampedPrefix]:
        current_prefix = self.current_prefix

        return [
            tp for tp in
            self.s3u.get_timestamped_prefixes(
                base_prefix=self.checkpointed_dir_path,
                after_timestamp=self.current_checkpoint_ts or (
                    current_prefix.timestamp
                    if current_prefix
                    else None
                )
            )
            if self.is_prefix_ready_for_processing(tp)
        ]

    @remaining_prefixes.setter
    def remaining_prefixes(self, new_value: t.Iterable[TimestampedPrefix]) -> None:
        raise NotImplemented("Unable to set next prefix, set current_checkpoint_ts to value preceding or delete it altogether")

    @remaining_prefixes.deleter
    def remaining_prefixes(self) -> None:
        raise NotImplemented("Unable to delete remaining prefixes, set current_checkpoint_ts to value after last prefix or delete them at source")

    @property
    def next_prefix(self) -> t.Optional[TimestampedPrefix]:
        remaining_prefixes = self.remaining_prefixes
        if remaining_prefixes:
            return remaining_prefixes[0]
        else:
            return None

    @next_prefix.setter
    def next_prefix(self, new_value: TimestampedPrefix) -> None:
        raise NotImplemented("Unable to set next prefix. Set current_checkpoint_ts to value preceding this prefix.")

    @next_prefix.deleter
    def next_prefix(self) -> None:
        raise NotImplemented("Unable to delete next prefix. Delete it from storage manually if need be")

    def pull_prefix(self, prefix: TimestampedPrefix, local_dir: t.Union[str, Path], max_threads: int = -1):
        Path(local_dir).mkdir(exist_ok=True)

        self.s3u.download_dir(
            local_dir=str(local_dir),
            prefix_path=prefix.prefix_path,
            max_threads=max_threads
        )

    @contextmanager
    def checkpoint_download_manager(self,
                                    base_download_dir: t.Union[str, Path],
                                    advance_checkpoint: bool = False,
                                    limit: t.Optional[int] = None,
                                    max_threads: int = -1
                                    ) -> t.ContextManager[t.List[DownloadedPrefix]]:
        """Download <n=limit> checkpoints to local directory and advance checkpoint after the fact
        :param base_download_dir: Local base directory where checkpointed dirs will be downloaded
        :param advance_checkpoint: Whether or not the checkpoint file should be updated after the downloads
        :param limit: max number of checkpointed dirs to download
        :param max_threads: maximum number of threads for multithreading
        :return: List of tuples (local_downloaded_dir, timestamp_prefix)
        """

        prefixes = self.remaining_prefixes[:limit]
        download_dir_paths = []
        base_download_dir = Path(base_download_dir).resolve()
        if not base_download_dir.is_dir():
            raise ValueError(f"Provided base_download_dir does not exist: {base_download_dir!s}")

        try:
            for prefix in prefixes:
                download_dir = Path(base_download_dir, Path(prefix.prefix_path).name)
                self.pull_prefix(
                    prefix=prefix,
                    local_dir=download_dir,
                    max_threads=max_threads
                )
                download_dir_paths.append(download_dir)

            yield [
                DownloadedPrefix(local_path=local_path, timestamped_prefix=prefix)
                for local_path, prefix in zip(download_dir_paths, prefixes)
            ]
        finally:
            if prefixes and advance_checkpoint:
                self.current_checkpoint_ts = prefixes[-1].timestamp