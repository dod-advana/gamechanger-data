import click
from .utils import LoadManager
import typing as t
from dataPipelines.gc_ingest.config import Config
from dataPipelines.gc_ingest.common_cli_options import pass_bucket_name_option
import datetime as dt
import functools
from pathlib import Path
import json


def pass_core_load_cli_options(f):
    @click.option(
        '--load-archive-base-prefix',
        type=str,
        help="S3 base prefix for storing loaded files",
        required=True
    )
    @functools.wraps(f)
    def wf(*args, **kwargs):
        return f(*args, **kwargs)
    return wf


@click.group(name="load")
@pass_core_load_cli_options
@pass_bucket_name_option
@click.pass_context
def load_cli(ctx: click.Context, load_archive_base_prefix: str, bucket_name: str):
    """Ingest Docs & Register them in the DB"""
    ctx.obj = LoadManager(
        load_archive_base_prefix=load_archive_base_prefix,
        bucket_name=bucket_name
    )


pass_lm = click.make_pass_decorator(LoadManager)



@load_cli.command()
@click.option(
    '--raw-doc-dir',
    type=click.Path(
        exists=True,
        dir_okay=True,
        file_okay=False,
        resolve_path=True
    ),
    help="Path to local directory with raw docs",
    required=True
)
@click.option(
    '--metadata-doc-dir',
    type=click.Path(
        exists=True,
        dir_okay=True,
        file_okay=False,
        resolve_path=True
    ),
    help="Path to directory with metadata files corresponding to raw docs"
)
@click.option(
    '--parsed-doc-dir',
    type=click.Path(
        exists=True,
        dir_okay=True,
        file_okay=False,
        resolve_path=True
    ),
    help="Path to directory with parsed files corresponding to raw docs"
)
@click.option(
    '--timestamp',
    type=click.DateTime(),
    help="Timestamp that will be used to mark this load batch and relevant s3 paths",
    default=Config.default_batch_timestamp_str
)
@click.option(
    '--skip-s3-upload',
    type=bool,
    default=False,
    show_default=True,
    help="Don't upload any files to s3"
)
@click.option(
    '--skip-db-update',
    type=bool,
    default=False,
    show_default=True,
    help="Don't make any DB updates"
)
@pass_lm
def local(lm: LoadManager,
          raw_doc_dir: str,
          metadata_doc_dir: t.Optional[str],
          parsed_doc_dir: t.Optional[str],
          timestamp: dt.datetime,
          skip_s3_upload: bool,
          skip_db_update: bool) -> None:
    """Ingest from a local directory"""

    lm.load(
        raw_dir=raw_doc_dir,
        parsed_dir=parsed_doc_dir,
        metadata_dir=metadata_doc_dir,
        ingest_ts=timestamp,
        update_s3=not skip_s3_upload,
        update_db=not skip_db_update
    )


def remove_docs_from_db(lm: LoadManager, removal_list: list):
    for (filename, doc_name) in removal_list:
        lm.remove_from_db(filename=filename, doc_name=doc_name)


@load_cli.command("remove-from-db")
@pass_lm
@click.option(
        '--input-json-path',
        type=str,
        help="Input JSON list path, this should resemble the metadata, at least having a 'doc_name' field " +
             "and a 'downloadable_items'.'doc_type' field",
        required=True
)
def remove_docs_from_db_wrapper(lm: LoadManager, input_json_path: str ):
    input_json = Path(input_json_path).resolve()
    if not input_json.exists():
        print("No valid input json")
        return
    removal_list=[]
    print("REMOVING DOCS FROM DB")
    with input_json.open(mode="r") as f:
        for json_str in f.readlines():
            if not json_str.strip():
                continue
            else:
                try:
                    j_dict = json.loads(json_str)
                except json.decoder.JSONDecodeError:
                    print("Encountered JSON decode error while parsing crawler output.")
                    continue
                doc_name = j_dict["doc_name"]
                filename = j_dict.get("filename", "")
                removal_list.append((filename,doc_name))
    remove_docs_from_db(
        lm=lm,
        removal_list=removal_list
    )

@load_cli.command()
@pass_lm
def json_metadata_to_json(lm: LoadManager):
    lm.json_metadata_to_json()


@load_cli.command()
@pass_lm
def json_metadata_to_string(lm: LoadManager):
    lm.json_metadata_to_string()
