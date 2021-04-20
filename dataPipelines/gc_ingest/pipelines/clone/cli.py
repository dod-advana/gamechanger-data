import click
from dataPipelines.gc_ingest.tools.checkpoint.utils import CheckpointManager
from dataPipelines.gc_ingest.tools.snapshot.utils import SnapshotManager
from dataPipelines.gc_ingest.tools.load.utils import LoadManager
from common.document_parser.cli import pdf_to_json
from dataPipelines.gc_elasticsearch_publisher.gc_elasticsearch_publisher import ConfiguredElasticsearchPublisher
from dataPipelines.gc_ingest.config import Config
from pathlib import Path
import typing as t
import shutil
import datetime as dt
import sys


def announce(text: str):
    print("#### PIPELINE INFO #### " + text, file=sys.stderr)

@click.group(name='clone')
def clone_cli():
    """Clone Pipelines"""
    pass

@clone_cli.command(name='ingest')
def ingest():
    """Clone Ingest Pipeline"""
    pass