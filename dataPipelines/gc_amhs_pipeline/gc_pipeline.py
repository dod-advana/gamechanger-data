from time import time
import os
from typing import Union
from pathlib import Path
import click
import csv
from elasticsearch import helpers, Elasticsearch
import json
from .conf import Conf
from common.document_parser.parsers.amhs import amhs_parser as parser


@click.command()
@click.option(
    "-d",
    "--directory",
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
@click.option("--alias", required=False, default="None", type=str, help="set alias")
def run(es_index: str, directory: str, es_host: str, es_port: str, alias: str):
    print("Starting Gamechanger AMHS Pipeline")
    start = time()
    # Download PDF and metadata files

    pdf_reader(directory, es_host, es_port, es_index, alias)

    end = time()
    print(f"Total time -- It took {end - start} seconds!")
    print("DONE!!!!!!")


def pdf_reader(file_name, host, port, index, alias):
    print(index)
    es = Conf.ch.es_client
    helpers.bulk(es, get_orders(file_name), index=index)
    if alias != "None":
        es.indices.put_alias(index=index, name=alias)


def get_orders(filename):
    order_list = parser.extract_document(filename)
    for doc in order_list:
        yield doc


if __name__ == "__main__":
    run()
