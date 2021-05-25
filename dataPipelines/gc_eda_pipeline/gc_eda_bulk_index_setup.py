import click
import json
import os
from dataPipelines.gc_eda_pipeline.indexer.indexer import create_index
from dataPipelines.gc_eda_pipeline.utils.eda_utils import read_extension_conf
import csv
from csv import writer

@click.command()
@click.option(
    '-s',
    '--staging-folder',
    help="A temp folder for which the eda data will be staged for processing.",
    required=True,
    type=str,
)
@click.option(
    '--input-list-file',
    required=True,
    type=str
)
@click.option(
    '--output-file',
    required=True,
    type=str
)

def run(staging_folder: str, input_list_file: str, output_file: str):
    print("Starting Gamechanger Configuration")
    # Load Extensions configuration files.
    data_conf_filter = read_extension_conf()

    eda_audit_publisher = create_index(index_name=data_conf_filter['eda']['audit_index'],ingest_dir="", alias=data_conf_filter['eda']['audit_index_alias'])

    eda_publisher = create_index(index_name=data_conf_filter['eda']['eda_index'],ingest_dir="", alias=data_conf_filter['eda']['eda_index_alias'])








def append_list_as_row(file_name, list_of_elem):
    # Open file in append mode
    with open(file_name, 'a+', newline='') as write_obj:
        # Create a writer object from csv module
        csv_writer = writer(write_obj)
        # Add contents of list as last row in the csv file
        csv_writer.writerow(list_of_elem)

if __name__ == '__main__':
    run()
