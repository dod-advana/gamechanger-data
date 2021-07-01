import click
from dev_tools.universal_test_harness.config import Config
from common.utils.s3 import S3Utils
from botocore.client import ClientError
from pathlib import Path


@click.group('s3')
def s3_cli():
    """S3 Tools"""
    pass


@s3_cli.command('reset')
def reset():
    """Init S3 Buckets and Prime with Test Files"""
    s3u = S3Utils(Config.ch)
    try:
        Config.ch.s3_client.head_bucket(Bucket=s3u.bucket)
    except ClientError:
        Config.ch.s3_client.create_bucket(Bucket=s3u.bucket)

    s3u.delete_prefix("/")

    print(Config.CRAWLER_OUTPUT_PATH)
    for d in Path(Config.CRAWLER_OUTPUT_PATH).iterdir():
        s3u.upload_dir(
            local_dir=(d.resolve()),
            prefix_path='gamechanger/external-uploads/crawler-downloader/' + d.name
        )

    print(Config.PARSED_OUTPUT_PATH)
    for d in Path(Config.PARSED_OUTPUT_PATH).iterdir():
        s3u.upload_dir(
            local_dir=(d.resolve()),
            prefix_path='gamechanger/external-uploads/parsed-crawler-downloader/' + d.name
        )

@s3_cli.command('peek')
def peek():
    """Peek parts of S3 hierarchy"""
    s3u = S3Utils(Config.ch)

    for s in s3u.iter_object_paths_at_prefix('/'):
        print(s)


@s3_cli.command('purge')
def purge():
    """Purge S3 Contents"""
    s3u = S3Utils(Config.ch)
    try:
        Config.ch.s3_client.head_bucket(Bucket=s3u.bucket)
    except ClientError:
        Config.ch.s3_client.create_bucket(Bucket=s3u.bucket)

    s3u.delete_prefix("/")