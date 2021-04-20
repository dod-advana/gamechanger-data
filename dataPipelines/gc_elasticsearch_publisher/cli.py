import click
from time import time
from dataPipelines.gc_elasticsearch_publisher.gc_elasticsearch_publisher import (ConfiguredElasticsearchPublisher, ConfiguredEntityPublisher)
from configuration import RENDERED_DIR
import os
from . import DEFAULT_ENTITIY_CSV_PATH


@click.group()
def cli():
    pass


@cli.command()
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
    '''comment'''
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