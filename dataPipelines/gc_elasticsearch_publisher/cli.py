import click
from time import time
from dataPipelines.gc_elasticsearch_publisher.gc_elasticsearch_publisher import (ConfiguredElasticsearchPublisher, ConfiguredEntityPublisher)
from configuration import RENDERED_DIR
import os
from . import DEFAULT_ENTITIY_CSV_PATH
from pathlib import Path
import json

@click.group()
def cli():
    pass

@cli.command(name='setup-index')
@click.option(
    "-i",
    "--index_name",
    help="The Elasticsearch Schema that will be created/used",
    default="elasticsearch",
    required=True,
)
@click.option(
    "-a",
    "--alias",
    help="The Elasticsearch Alias that will be created/used. If not is provided, no alias will be used.",
    default="",
    required=False,
)
@click.option(
    "-m",
    "--mapping_file",
    help="ES Index & Settings file",
    type=click.Path(exists=True, file_okay=True,
                    dir_okay=False, resolve_path=True),
    default=os.path.join(RENDERED_DIR, "elasticsearch", "index.json"),
    show_default=True,
)
def setup_index(index_name: str, alias: str, mapping_file: str) -> None:
    """Create & configure ES index with (optional) alias"""
    publisher = ConfiguredElasticsearchPublisher(
        index_name=index_name,
        ingest_dir=None,
        mapping_file=mapping_file,
        alias=alias,
    )

    publisher.create_index()
    if alias:
        publisher.update_alias()


@cli.command(name='run')
@click.option(
    "-i",
    "--index_name",
    help="The Elasticsearch Schema that will be created/used",
    default="elasticsearch",
    required=True,
)
@click.option(
    "-a",
    "--alias",
    help="The Elasticsearch Alias that will be created/used. If not is provided, no alias will be used.",
    default="",
    required=False,
)
@click.option(
    "-m",
    "--mapping_file",
    help="ES Index & Settings file",
    type=click.Path(exists=True, file_okay=True,
                    dir_okay=False, resolve_path=True),
    default=os.path.join(RENDERED_DIR, "elasticsearch", "index.json"),
    show_default=True,
)
@click.option(
    "-d",
    "--ingest_dir",
    help="test",
    type=click.Path(exists=True, file_okay=False,
                    dir_okay=True, resolve_path=True),
    required=False,
)
def run(index_name: str, alias: str, mapping_file: str, ingest_dir) -> None:
    """Index dir of files into elasticsearch."""
    start = time()
    publisher = ConfiguredElasticsearchPublisher(
        index_name=index_name,
        ingest_dir=ingest_dir,
        mapping_file=mapping_file,
        alias=alias,
    )

    publisher.create_index()
    if ingest_dir:
        publisher.index_jsons()
    if alias:
        publisher.update_alias()

    end = time()
    print(f"Total Index time -- It took {end - start} seconds!")


def remove_docs_from_index(index_name: str, removal_list: list) -> None:
    publisher = ConfiguredElasticsearchPublisher(
        index_name=index_name,
        ingest_dir=""
    )
    records = [r.stem for r in removal_list]
    publisher.delete_record(records=records)


@cli.command(name='remove-docs-from-es')
@click.option(
    "-i",
    "--index-name",
    help="The Elasticsearch Schema that will be created/used",
    default="elasticsearch",
    type=str,
    required=True,
)
@click.option(
        '--input-json-path',
        type=str,
        help="Input JSON list path of docs to be deleted, " +
             "this should resemble the metadata, at least having a 'doc_name' field " +
             "and a 'downloadable_items'.'doc_type' field",
        required=True
    )
def remove_docs_from_es(index_name: str, input_json_path: str) -> None:
    input_json = Path(input_json_path).resolve()
    if not input_json.exists():
        print("No valid input json")
        return

    print("REMOVING DOCS FROM ES")
    records = []
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
            filename = Path(j_dict.get("filename",
                                       j_dict["doc_name"] + "." + j_dict["downloadable_items"].pop()["doc_type"]))
            records.append(filename)
    remove_docs_from_index(
        index_name=index_name,
        removal_list=records
    )


@cli.command(name="entity-insert")
@click.option(
    '-i',
    '--index_name',
    help='The Elasticsearch Schema that will be created/used',
    default="elasticsearch",
    required=True,
)
@click.option(
    '-a',
    '--alias',
    help='The Elasticsearch Alias that will be created/used. If not is provided, no alias will be used.',
    default="",
    required=False,
)
@click.option(
    '-m',
    '--mapping_file',
    help='ES Index & Settings file',
    type=click.Path(exists=True, file_okay=True, dir_okay=False, resolve_path=True),
    default=os.path.join(RENDERED_DIR, "elasticsearch", "index.json"),
    show_default=True
)
@click.option(
    '--entity-csv-path',
    help='test',
    type=click.Path(exists=True, file_okay=True, dir_okay=False, resolve_path=True),
    required=False,
    default=DEFAULT_ENTITIY_CSV_PATH,
    show_default=True
)
def entity_insert(index_name: str, alias: str, mapping_file: str, entity_csv_path: str) -> None:
    '''Populate the entities index.'''
    start = time()
    publisher = ConfiguredEntityPublisher(
        index_name=index_name,
        entity_csv_path=entity_csv_path,
        mapping_file=mapping_file,
        alias=alias
    )

    publisher.create_index()
    publisher.index_jsons()
    if alias:
        publisher.update_alias()

    end = time()
    print(f'Total Index time -- It took {end - start} seconds!')