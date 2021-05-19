from botocore.exceptions import ClientError
from configuration.helpers import ConnectionHelper
from typing import Optional, Union, List, Iterable, Tuple, Dict, Any
from pathlib import Path
import datetime
from concurrent.futures import ThreadPoolExecutor
import multiprocessing
from common.utils.parsers import parse_timestamp
import re
from common.utils.parsers import parse_formatted_timestamp
import os
from .text_utils import size_fmt
import datetime as dt
import typing as t


class TimestampedPrefix:
    """S3 prefix constructed with a particular timestamp"""
    def __init__(self, prefix_path: str, timestamp: datetime.datetime, timestamp_str: str):
        self.prefix_path = prefix_path
        self.timestamp = timestamp
        self.timestamp_str = timestamp_str

# TODO
#   relying on S3-compatible storage is not ideal
#   there should be a more abstract storage-provider interface
#   to enable use of local or arbitrary storage backends
# TODO
#   it might be desirable to have a mechanism for specifying rules for s3 operations
#   to avoid scenarios like accidentally deleting/copying/clobbering files because of
#   programming mistakes
class S3Utils:
    """S3 utils for common operations"""
    TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S"
    TIMESTAMPED_PATH_REGEX = re.compile(
        pattern=r"""
                    (?P<path_base>.*/)
                    (?P<timestamp>
                            (?P<ts_date>
                                (?P<ts_year>\d{4})-
                                (?P<ts_month>\d{2})-
                                (?P<ts_day>\d{2})
                            )
                            T
                            (?P<ts_time>
                                (?P<ts_hour>\d{2}):
                                (?P<ts_minute>\d{2}):
                                (?P<ts_second>\d{2})
                            )
                    )
                    /$
                """,
        flags=re.VERBOSE,
    )

    def __init__(self, ch: ConnectionHelper, bucket: Optional[str] = None):
        self.ch = ch
        self.bucket = bucket or self.ch.conf['aws']['bucket_name']

    @staticmethod
    def ensure_tailing_slash(prefix: Optional[Union[str, Path]]) -> str:
        """Ensure prefix looks like a path, i.e. ends with a '/'"""
        str_prefix = str(prefix) if prefix else ""
        if not str_prefix:
            return ""
        return re.sub(pattern=r"""(?<!/)$""", repl=r"/", string=str_prefix)

    @staticmethod
    def path_join(*args: str) -> str:
        """Join parts of s3 url path together"""
        str_joined = re.sub(pattern=r"""(/)+""", repl=r"\1", string="/".join(args))
        str_sans_leading_slashes = str_joined[1:] if str_joined.startswith('/') else str_joined
        return str_sans_leading_slashes

    @staticmethod
    def format_as_prefix(prefix: str) -> str:
        """Format string as prefix"""
        prefix_with_tailing_slash = S3Utils.ensure_tailing_slash(prefix)
        prefix_in_proper_path_format = S3Utils.path_join(prefix_with_tailing_slash)
        return prefix_in_proper_path_format

    @staticmethod
    def get_prefix_at_ts(base_prefix: str, ts: t.Union[dt.datetime, str], ts_fmt: str = TIMESTAMP_FORMAT) -> str:
        """Get prefix for a given timestamp"""
        ts = parse_timestamp(ts=ts, raise_parse_error=True)
        base_prefix = S3Utils.format_as_prefix(base_prefix)
        return S3Utils.path_join(base_prefix, ts.strftime(ts_fmt))

    def iter_object_paths_at_prefix(self, prefix: str, bucket: Optional[str] = None) -> Iterable[str]:
        """Iterate over object keys at prefix"""
        bucket_name = bucket or self.bucket
        for obj_summary in self.ch.s3_resource.Bucket(bucket_name).objects.filter(Prefix=prefix):
            yield obj_summary.key

    def get_prefix_stats(self, prefix: str, bucket: Optional[str] = None) -> Dict[str, Any]:
        """Get summary stats about contents of the prefix"""
        stats = {
            'obj_count': 0,
            'total_size_bytes': 0,
            'total_size': '0'
        }

        bucket_name = bucket or self.bucket
        for obj_summary in self.ch.s3_resource.Bucket(bucket_name).objects.filter(Prefix=prefix):
            stats['obj_count'] += 1
            stats['total_size_bytes'] += obj_summary.meta.data.get('Size', 0)
        stats['total_size'] = size_fmt(stats['total_size_bytes'])

        return stats

    def upload_file(
            self,
            file: Union[str, Path],
            object_name: Optional[str] = None,
            object_prefix: Optional[str] = None,
            bucket: Optional[str] = None) -> str:
        """Upload a file to an S3 bucket

        :param ch: configuration.ConnectionHelper
        :param file: Path to file
        :param object_name: S3 object name (can be full object_path)
        :param object_prefix: Prefix to s3 object, prepended to final object path with '/'
        :param bucket: Bucket to upload to
        :return: Uploaded object name
        """
        file_path = Path(file).resolve()
        file_name = os.path.basename(file_path)
        object_path = self.path_join(
            self.format_as_prefix(object_prefix),
            object_name or file_path.name
        )

        bucket_name = bucket or self.bucket

        # Upload the file
        s3_client = self.ch.s3_client
        s3_client.upload_file(str(file_path), bucket_name, object_path)

        return object_path

    def download_file(
            self,
            object_path: str,
            file: Union[str, Path],
            bucket: Optional[str] = None) -> Optional[Path]:
        """Download file from S3 bucket

        :param ch: configuration.ConnectionHelper
        :param object_path: full name of object to download (prefix & all)
        :param file: Path to file on local disk
        :param bucket: Bucket name
        :return: Path of the downloaded file
        """
        file_path = Path(file).resolve()
        bucket_name = bucket or self.bucket

        # Upload the file
        s3_client = self.ch.s3_client
        s3_client.download_file(self.bucket, object_path, str(file_path))

        return file_path

    def object_exists(self, object_path: str, bucket: Optional[str] = None) -> bool:
        """Check if s3 object exists at given path
        :param object_path: Full s3 path to object (sans bucket name)
        :param bucket: Bucket name
        :return: True/False
        """
        bucket_name = bucket or self.bucket
        try:
            self.ch.s3_client.head_object(Bucket=bucket_name, Key=object_path)
            return True
        except ClientError:
            # Not found
            return False

    def prefix_exists(self, prefix_path: str, bucket: Optional[str] = None) -> bool:
        """Check if files with given s3 path prefix exist
        :param prefix_path: S3 prefix
        :param bucket: Bucket name
        :return: True/False
        """
        bucket_name = bucket or self.bucket
        if next(iter(self.iter_object_paths_at_prefix(prefix=prefix_path, bucket=bucket_name)), None):
            return True
        else:
            return False

    def download_dir(self,
                     local_dir: Union[str, Path],
                     prefix_path: str = "",
                     bucket: Optional[str] = None,
                     max_threads: int = 1) -> None:
        """Downloads recursively the given S3 path to the target directory.
        :param local_dir: path to local dir
        :param prefix_path: the folder path in the s3 bucket
        :param bucket: Bucket name
        :param max_threads: number of threads for multithreading
        """
        local_dir_path = Path(local_dir).resolve()
        s3_client = self.ch.s3_client
        s3_resource = self.ch.s3_resource
        print(local_dir_path)
        # Handle missing / at end of prefix
        if not prefix_path.endswith('/'):
            prefix_path += '/'

        bucket_name = bucket or self.bucket

        # defining an inner function for the download commands for ease of running the multithreading command
        # makes it so that everything's in one place when I run executor.map() if multithreading
        def dl_inner_func(obpath):
            path, filename = os.path.split(obpath)
            if not obpath.endswith("/"):
                tmp = path + "/"
                if tmp.replace(prefix_path, "", 1) is None:
                    self.download_file(bucket=bucket_name, object_path=obpath, file=local_dir + "/" + filename)
                else:
                    sub_path = tmp.replace(prefix_path, "", 1)
                    base_path = Path(local_dir, sub_path)
                    base_path.mkdir(exist_ok=True,parents=True)
                    file_path = Path(base_path, filename)
                    self.download_file(bucket=bucket_name, object_path=obpath, file=str(file_path))

        tasks_to_do = self.iter_object_paths_at_prefix(prefix=prefix_path)

        # if we use all available resources
        # NOT recommended. This uses all computing power at once, will probably crash if big directory
        if max_threads < 0:
            max_workers = multiprocessing.cpu_count()

        # if we don't use multithreading or if we do partitioned multithreading
        elif max_threads >= 1:
            max_workers = max_threads

        # else, bad value inserted for max_threads
        else:
            raise ValueError(f"Invalid max_threads value given: ${max_threads}")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            executor.map(dl_inner_func, (tasks for tasks in tasks_to_do))

    def upload_dir(self,
                   local_dir: Union[str, Path],
                   prefix_path: str = "",
                   bucket: Optional[str] = None,
                   max_threads: int = 1) -> List[str]:
        """Upload all files in the directory to S3
        :param local_dir: path to local dir
        :param prefix_path: S3 prefix for uploaded objects
        :param bucket: Bucket name
        :param max_threads: number of threads for multithreading
        :return: List of uploaded object names
        """
        local_dir_path = Path(local_dir).resolve()
        uploaded_objects: List[str] = []

        # defining an inner function for the upload commands for ease of running the multithreading command
        # makes it so that everything's in one place when I run executor.map() if multithreading
        def up_inner_func(locpath):
            if locpath.is_file():
                relative_parent_dir_path = str(locpath.parent.relative_to(local_dir_path))
                if relative_parent_dir_path in ['.','..','/']:
                    relative_parent_dir_path=""

                final_prefix = self.path_join(
                    self.format_as_prefix(prefix_path),
                    self.format_as_prefix(relative_parent_dir_path)
                )

                print(f"Uploading {locpath.name} to prefix {prefix_path}")
                self.upload_file(file=locpath, object_prefix=prefix_path, bucket=(bucket or self.bucket))

                return os.path.join(final_prefix, locpath.name)

        tasks_to_do = local_dir_path.rglob("*")

        # if we use all available resources
        # NOT recommended. This uses all computing power at once, will probably crash if big directory
        if max_threads < 0:
            max_workers = multiprocessing.cpu_count()

        # if we don't use multithreading or if we do partitioned multithreading
        elif max_threads >= 1:
            max_workers = max_threads

        # else, bad value inserted for max_threads
        else:
            raise ValueError(f"Invalid max_threads value given: ${max_threads}")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            r = executor.map(up_inner_func, (tasks for tasks in tasks_to_do))
            for result in r:
                if result:
                    uploaded_objects.append(result)

        return uploaded_objects

    def copy_prefix(self, src_prefix: str, dst_prefix: str, bucket: Optional[str] = None) -> List[str]:
        """Recursively copies all objects from given src prefix to corresponding paths on destination prefix
        :param src_prefix: Source prefix
        :param dst_prefix: Destination prefix
        :param bucket: Bucket name
        :return: dst_object_paths
        """
        s3_resource = self.ch.s3_resource
        dst_obj_paths: List[str] = []

        bucket_name = bucket or self.bucket
        for obj_path in self.iter_object_paths_at_prefix(prefix = src_prefix):
            new_obj_path = (
                    self.format_as_prefix(dst_prefix)
                    + str(Path(obj_path).relative_to(src_prefix))
            )

            print(f"Copying {obj_path} to {new_obj_path}")

            # self.copy_file(src_obj_path=obj_path, dst_obj_path=new_obj_path, bucket=bucket_name)

            s3_resource.Object(
                bucket_name=bucket_name,
                key=new_obj_path
            ).copy_from(
                CopySource={'Bucket': bucket_name, 'Key': obj_path}
            )

            dst_obj_paths.append(new_obj_path)
        return dst_obj_paths

    def delete_object(self, object_path: str, bucket: Optional[str] = None) -> None:
        """Delete s3 object at given path
        :param object_path: Full object key
        :param bucket: Bucket name
        :return: N/A - deletes object, no error if object doesn't exist
        """
        bucket_name = bucket or self.bucket
        s3_resource = self.ch.s3_resource

        if self.object_exists(object_path=object_path, bucket=bucket_name):
            s3_resource.Object(bucket_name, object_path).delete()

    def delete_prefix(self, prefix: str, bucket: Optional[str] = None, max_threads: int = 1) -> List[str]:
        """Delete all S3 objects with given prefix
        :param prefix: S3 obj prefix
        :param bucket: Bucket name
        :param max_threads: number of threads for multithreading
        :return: List of deleted object paths
        """

        bucket_name = bucket or self.bucket
        deleted_object_paths: List[str] = []
        tasks_to_do = self.iter_object_paths_at_prefix(prefix=prefix, bucket=bucket_name)

        # if we use all available resources
        # NOT recommended. This uses all computing power at once, will probably crash if big directory
        if max_threads < 0:
            max_workers = multiprocessing.cpu_count()

        # if we don't use multithreading or if we do partitioned multithreading
        elif max_threads >= 1:
            max_workers = max_threads

        # else, bad value inserted for max_threads
        else:
            raise ValueError(f"Invalid max_threads value given: ${max_threads}")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            r = executor.map(self.delete_object,
                             (tasks for tasks in tasks_to_do),
                             (bucket_name for _ in tasks_to_do))
            for result in r:
                if result:
                    deleted_object_paths.append(result[0])

        return deleted_object_paths

    def move_prefix(self, old_prefix: str, new_prefix: str, bucket: Optional[str] = None) -> List[str]:
        """Move all objects from old prefix to new prefix (copies then deletes)
        :param old_prefix: Old S3 prefix
        :param new_prefix: New S3 prefix
        :param bucket: Bucket name
        :return: List of object paths at the next prefix
        """
        bucket_name = bucket or self.bucket

        # TODO: if there are async operations going on to the same old_prefix path,
        #   it may be desirable to only delete objects that existed at beginning of copy operation
        #   to avoid deleting objects that were never copied to the new prefix
        new_paths = self.copy_prefix(src_prefix=old_prefix, dst_prefix=new_prefix, bucket=bucket_name)
        self.delete_prefix(prefix=old_prefix, bucket=bucket_name)

        return new_paths

    def get_checkpoint_ts(self,
                          checkpoint_path: str,
                          bucket: Optional[str] = None) -> Optional[datetime.datetime]:
        """Get timestamp from the checkpoint file
        :param checkpoint_path: Path to timestamp checkpoint file
        :param bucket: Bucket name
        :return: Timestamp from the checkpoint file, if one exists
        """

        bucket_name = bucket or self.bucket
        s3_resource = self.ch.s3_resource

        if not self.object_exists(object_path=checkpoint_path, bucket=bucket_name):
            return None

        response: Dict[str, Any] = s3_resource.Object(
            bucket_name,
            checkpoint_path
        ).get()

        ts_str = response['Body'].read().decode(encoding="utf-8")

        return parse_timestamp(ts_str)

    def update_checkpoint(self,
                          timestamp: Union[str, datetime.datetime],
                          checkpoint_path: str,
                          bucket: Optional[str] = None) -> str:
        """Update the checkpoint file
        :param timestamp: datetime.datetime or str timestamp in S3Utils.TIMESTAMP_FORMAT
        :param checkpoint_path: full s3 path to checkpoint file, sans bucket name
        :param bucket: Bucket name
        :return: S3 path to the checkpoint file
        """
        s3_resource = self.ch.s3_resource
        bucket_name = bucket or self.bucket

        ts_str = (
            timestamp
            if isinstance(timestamp, str)
            else timestamp.strftime(self.TIMESTAMP_FORMAT)
        )

        # bail on invalid timestamp fmt
        try:
            datetime.datetime.strptime(ts_str, self.TIMESTAMP_FORMAT)
        except ValueError:
            raise

        s3_obj = s3_resource.Object(bucket_name, checkpoint_path)
        s3_obj.put(Body=ts_str)

        return checkpoint_path

    def parse_timestamp_from_prefix(self, timestamped_prefix: str) -> Optional[datetime.datetime]:
        """Parse timestamp from the given timestamped prefix
        :param timestamped_prefix: s3 prefix with timestamp at the end
        :return: datetime.datetime if there's a correct timestamp, else None
        """
        return (
            self.TIMESTAMPED_PATH_REGEX.match(timestamped_prefix).groupdict()["timestamp"]
            if self.TIMESTAMPED_PATH_REGEX.match(timestamped_prefix)
            else None
        )

    def get_timestamped_prefixes(self,
                                 base_prefix: str,
                                 after_timestamp: Optional[Union[datetime.datetime, str]] = None,
                                 bucket: Optional[str] = None) -> List[TimestampedPrefix]:
        """Get S3 prefixes that conform to the timestamp format & regex
        :param base_prefix: Base/parent prefix for timestamped prefixes
        :param after_timestamp: Only return prefixes after the given timestamp
        :param bucket: Bucket name
        :return: List of valid timestamped prefixes
        """
        s3_client = self.ch.s3_client

        _base_prefix = self.format_as_prefix(base_prefix)
        if not isinstance(after_timestamp, datetime.datetime):
            after_timestamp = parse_formatted_timestamp(after_timestamp, self.TIMESTAMP_FORMAT)

        bucket_name = bucket or self.bucket
        default_delimiter = "/"


        valid_timestamped_prefixes = [
            TimestampedPrefix(
                prefix_path=p["Prefix"],
                timestamp=datetime.datetime.strptime(
                    self.TIMESTAMPED_PATH_REGEX.match(p["Prefix"]).groupdict()["timestamp"],
                    self.TIMESTAMP_FORMAT,
                ),
                timestamp_str=self.TIMESTAMPED_PATH_REGEX.match(p["Prefix"]).groupdict()["timestamp"]
            )
            for p in s3_client.list_objects(
                Bucket=bucket_name, Delimiter=default_delimiter, Prefix=_base_prefix
            ).get("CommonPrefixes", [])
            if self.TIMESTAMPED_PATH_REGEX.match(p["Prefix"])
        ]

        prefixes_after_last_checkpoint = [
            prefix
            for prefix in valid_timestamped_prefixes
            if prefix.timestamp > after_timestamp
        ] if after_timestamp else valid_timestamped_prefixes

        sorted_prefixes_after_last_checkpoint = sorted(
            prefixes_after_last_checkpoint, key=lambda prefix: prefix.timestamp
        )

        return sorted_prefixes_after_last_checkpoint
