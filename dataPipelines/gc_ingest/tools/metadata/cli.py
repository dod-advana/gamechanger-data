import click
from .metadata import create_metadata_from_manifest
import pandas as pd
import typing as t
from dataPipelines.gc_ingest.config import Config
from dataPipelines.gc_ingest.common_cli_options import pass_bucket_name_option
import datetime as dt
import functools
from pathlib import Path
import json


@click.command(name="metadata")
@click.option(
        '--manifest',
        type=str,
        help="manifest for creating metadata",
        required=True
    )
@click.option(
        '--local-dir',
        type=str,
        help="manifest for creating metadata",
        required=True
    )
def metadata_cli(manifest: str, local_dir: str):
    """Create metadata based on manifest"""
    output = Path(local_dir)
    input = Path(local_dir, manifest).resolve()
    if not input.exists():
        return
    df = pd.read_csv(input)
    insert_manifest = df[df['Process']=="Insert"].to_dict()
    create_metadata_from_manifest(manifest_dict=insert_manifest, output_dir=output)

