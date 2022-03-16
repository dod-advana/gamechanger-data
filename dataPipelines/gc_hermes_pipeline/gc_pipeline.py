from time import time
import os
from typing import Union
from pathlib import Path
import click
import csv
from elasticsearch import helpers, Elasticsearch
from .conf import Conf

@click.command()
@click.option(
    '-d',
    '--directory',
    help="The location of the csv file(s) to be indexed. Can be a single file or a directory",
    required=True,
    type=str,
)
@click.option(
    "--es-index",
    help="The index name to be use. If it does not exist it will be created",
    required=True,
    type=str,
)
@click.option(
    "--es-host",
    help="The host name to be used.",
    required=True,
    type=str,
)
@click.option(
    "--es-port",
    help="The port name to be used.",
    required=True,
    type=str,
)
@click.option(
    '--alias',
    required=False,
    default="None",
    type=str,
    help="set alias"
)
def run(es_index: str, directory: str,es_host: str,es_port: str, alias: str):
    print("Starting Gamechanger Hermes Pipeline")
    start = time()
    # Download PDF and metadata files

    csv_reader(directory, es_host, es_port, es_index, alias)


    end = time()
    print(f'Total time -- It took {end - start} seconds!')
    print("DONE!!!!!!")


def csv_reader(file_name,host,port,index,alias):
    print(index)
    es = Conf.ch.es_client
    if (str(file_name).endswith("csv")):
        with open(file_name, 'r') as outfile:
             reader = csv.DictReader(outfile)
             helpers.bulk(es, reader, index=index)
    elif (str(file_name).endswith("/")):
        pathlist = Path(file_name).rglob('*.csv')
        for path in pathlist:
             with open(path, 'r') as outfile:
                 reader = csv.DictReader(outfile)
                 helpers.bulk(es, reader, index=index)
    if alias is not "None":
        es.indices.put_alias(index=index,name=alias)


if __name__ == '__main__':
    run()
