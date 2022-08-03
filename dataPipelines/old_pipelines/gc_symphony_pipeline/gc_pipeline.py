from time import time
import os
from typing import Union
from pathlib import Path
from dataPipelines.gc_symphony_pipeline.conf import Conf
from dataPipelines.gc_elasticsearch_publisher.gc_elasticsearch_publisher import ConfiguredElasticsearchPublisher
from common.document_parser import Document
import click
import shutil
from datetime import date

@click.command()
@click.option(
    '-s',
    '--staging-folder',
    help="The folder in which the gamechanger data will be staged for processing. Just a tmp folder",
    required=True,
    type=str,
)
@click.option(
    "--skip-optional-ds",
    help="When generating the JSON should we skip optional DS process",
    required=True,
    type=bool,
    default=True
)
@click.option(
    "--es-index",
    help="The index name to be use. If it does not exist it will be created",
    required=True,
    type=str,
)
@click.option(
    "--es-alias",
    help="Alias to the elasticsearch index",
    required=True,
    type=str,
)
@click.option(
    '--aws-s3-json-prefix',
    required=True,
    type=str,
    default="gamechanger/projects/eda/json"
)
@click.option(
    '--aws-s3-pdf-prefix',
    required=True,
    type=str,
    default="gamechanger/projects/eda/json"
)
@click.option(
    '-p',
    '--multiprocess',
    required=False,
    default=-1,
    type=int,
    help="Multiprocessing. If treated like flag, will do max cores available. \
                if treated like option will take integer for number of cores.",
)
def run(staging_folder: str, skip_optional_ds: bool, aws_s3_json_prefix: str, aws_s3_pdf_prefix: str,
        multiprocess: int, es_index: str, es_alias: str):
    print("Starting Gamechanger Symphony Pipeline")
    start = time()

    # Download PDF and metadata files
    Conf.s3_utils.download_dir(local_dir=staging_folder + "/pdf/", prefix_path=aws_s3_pdf_prefix)

    # Generate Elasticsearch/Data Science JSONs
    print("Create JSONs for Elasticsearch and Data Science")
    run_docparser(staging_folder, staging_folder + "/pdf/", staging_folder + "/json", multiprocess, skip_optional_ds)
    shutil.make_archive(staging_folder+'/json_files'+date.today().strftime('%Y%m%d'), 'zip', staging_folder + "/json/")

    # Elasticsearch Indexer
    print("Index new files into Elasticsearch")
    run_indexer(index_name=es_index, alias=es_alias, ingest_dir=staging_folder + "/json")
    # Upload new ES/DS JSONS to S3
    print("Upload Elasticsearch jsons into S3")
    Conf.s3_utils.upload_file(file=staging_folder+'/json_files'+date.today().strftime('%Y%m%d')+'.zip', object_prefix=aws_s3_json_prefix)

    end = time()
    print(f'Total time -- It took {end - start} seconds!')
    print("DONE!!!!!!")


def run_indexer(index_name: str, alias: str, ingest_dir):
    ingest_dir_path = Path(ingest_dir).resolve()

    publisher = ConfiguredElasticsearchPublisher(index_name=str(index_name), ingest_dir=str(ingest_dir_path),
                                                 alias=str(alias))
    publisher.create_index()
    publisher.index_jsons()
    if alias:
        publisher.update_alias()


def run_docparser(staging_folder: Union[str, Path], input_dir: Union[Path, str],
                  output_dir: Union[Path, str],
                  multiprocess: int, skip_optional_ds: bool):
    input_dir_path = Path(input_dir).resolve()
    output_dir_path = Path(output_dir).resolve()
    staging_folder_path = Path(staging_folder).resolve()

    if not os.path.exists(str(staging_folder_path) + "/json/"):
        os.makedirs(str(staging_folder_path) + "/json/")

    Document.process_dir(dir_path=str(input_dir_path), out_dir=str(output_dir_path), clean=False,
                         meta_data=str(input_dir_path), multiprocess=multiprocess, skip_optional_ds=skip_optional_ds)


if __name__ == '__main__':
    run()
