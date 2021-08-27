import filecmp
import tarfile
from typing import Union
from pathlib import Path
import os
from shutil import copyfile
import shutil
import subprocess as sub
from time import time
from dataPipelines.gc_covid_pipeline.conf import Conf
from dataPipelines.gc_elasticsearch_publisher.gc_elasticsearch_publisher import ConfiguredElasticsearchPublisher
from dataPipelines.gc_covid_pipeline import COVIDDocument
from common.document_parser import Document
import re

import click


@click.command()
@click.option(
    '-s',
    '--staging-folder',
    help="The folder in which the covid 19 data will be staged for processing.",
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
    "--es-alias",
    help="Alias to the elasticsearch index",
    required=True,
    type=str,
)

@click.option(
    "--gc-project",
    help="The name of the project. Mostly of the time you will just use the default",
    type=str,
    default="covid19"
)
@click.option(
    "--s3-covd-dataset",
    help="The raw version of the COVD19 dataset located in S3,",
    type=str,
    required=True,
    default="bronze/gamechanger/projects/covid19/cord_dataset/cord-19.tar.gz"
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
def run(staging_folder: str, s3_covd_dataset: str,
        multiprocess: int, es_index: str, es_alias: str,
        gc_project: str = "covid19"):
    print("Starting COVID-19 Pipeline")
    start = time()

    if not os.path.exists(staging_folder + "/modification/"):
        os.makedirs(staging_folder + "/modification/")

    if not os.path.exists(staging_folder + "/modification/upload"):
        os.makedirs(staging_folder + "/modification/upload/")


    #  Pull down the skip_files_doc_parser.txt file
    print("Download Skip files doc parser file")
    Conf.s3_utils.download_file(file=staging_folder + "/modification/skip_file_doc_parser.txt",
                                bucket="advana-data-zone",
                                object_path="bronze/gamechanger/projects/" + gc_project + "/data-pipelines/orchestration/repo/skip_file_doc_parser.txt")

    # Download covid 19 dataset, currently being used
    print("Download Current covid 19 dataset")
    if Conf.s3_utils.object_exists(bucket="advana-data-zone",
                                   object_path="bronze/gamechanger/projects/" + gc_project + "/raw_jsons/pdf_json.tar.gz"):
        Conf.s3_utils.download_file(file=staging_folder + "/pdf_json.tar.gz", bucket="advana-data-zone",
                                    object_path="bronze/gamechanger/projects/" + gc_project + "/raw_jsons/pdf_json.tar.gz")
        with tarfile.open(staging_folder + "/pdf_json.tar.gz", "r:gz") as pdf_json_archive:
            pdf_json_archive.extractall(staging_folder)
    else:
        if not os.path.exists(staging_folder + "/pdf_json/"):
            os.makedirs(staging_folder + "/pdf_json/")

    if Conf.s3_utils.object_exists(bucket="advana-data-zone",
                                   object_path="bronze/gamechanger/projects/" + gc_project + "/raw_jsons/pmc_json.tar.gz"):
        Conf.s3_utils.download_file(file=staging_folder + "/pmc_json.tar.gz", bucket="advana-data-zone",
                                    object_path="bronze/gamechanger/projects/" + gc_project + "/raw_jsons/pmc_json.tar.gz")
        with tarfile.open(staging_folder + "/pmc_json.tar.gz", "r:gz") as pmc_json_archive:
            pmc_json_archive.extractall(staging_folder)
    else:
        if not os.path.exists(staging_folder + "/pmc_json/"):
            os.makedirs(staging_folder + "/pmc_json/")

    # Download the latest covid 19 dataset
    print("Download new COVID 19 dataset")
    print("bronze/gamechanger/projects/" + gc_project + "/cord_dataset/cord-19.tar.gz")
    Conf.s3_utils.download_file(file=staging_folder + "/cord-19.tar.gz",  bucket="advana-data-zone",
                                object_path=s3_covd_dataset)


    # Extract the CORD 19 dataset
    print("Extract new COVID 19 dataset")
    extract_cord_19_raw_file(staging_folder + "/cord-19.tar.gz", staging_folder)

    # Create CORD 19 Diff Folder for PDF/PMC JSON file
    print("Create Diff between old covid and new covid dataset")
    create_diff(staging_folder + "/pmc_json/", staging_folder + "/document_parses/pmc_json/", staging_folder,
                "pmc_json")
    create_diff(staging_folder + "/pdf_json/", staging_folder + "/document_parses/pdf_json/", staging_folder,
                "pdf_json")

    # Generate PDF files
    print("Create PDF files")
    run_pdf_generator(staging_folder, staging_folder + "/modification/pdf_json", staging_folder + "/metadata.csv",
                      staging_folder + "/modification/pdf/", staging_folder + "/modification/skip_file_doc_parser.txt",
                      multiprocess)
    run_pdf_generator(staging_folder, staging_folder + "/modification/pmc_json", staging_folder + "/metadata.csv",
                      staging_folder + "/modification/pdf", staging_folder + "/modification/skip_file_doc_parser.txt",
                      multiprocess)

    # Generate Elasticsearch/Data Science JSONs
    print("Create JSONs for Elasticsearch and Data Science")
    run_docparser(staging_folder, staging_folder + "/modification/pdf", staging_folder + "/modification/json",
                  multiprocess)

    # Elasticsearch Indexer
    print("Index new files into Elasticsearch")
    run_indexer(index_name=es_index, alias=es_alias, ingest_dir=staging_folder + "/modification/json")


    # Upload new PDF to S3
    print("Upload new PDF files into S3")
    Conf.s3_utils.upload_dir(local_dir=staging_folder + "/modification/pdf/", bucket="advana-data-zone",
                             prefix_path="bronze/gamechanger/projects/" + gc_project + "/pdf/")

    # Upload new ES/DS JSONS to S3
    print("Upload Elasticsearch jsons into S3")
    Conf.s3_utils.upload_dir(local_dir=staging_folder + "/modification/json/", bucket="advana-data-zone",
                             prefix_path="bronze/gamechanger/projects/" + gc_project + "/json/")

    # Delete Generated file no longer in the COVID dataset - Generated JSONs
    print("Delete file no longer need in S3 (PDF/Generated JSONs")
    delete_file_no_longer_need_in_s3(staging_folder + "/modification/files_to_remove.txt", gc_project)

    # Delete old records from Elasticsearch
    print("Delete file no longer need in S3 (PDF/Generated JSONs")
    delete_records_in_elasticsearch(file_list_records=staging_folder + "/modification/files_to_remove.txt",
                                    index_name=es_index,  ingest_dir=staging_folder + "/modification/json")

    # TAR new RAW JSONs
    print("TAR up new Raw JSONs")
    make_tarfile(output_filename="pdf_json.tar.gz", work_cmd=staging_folder + "/document_parses/", source_dir="pdf_json")
    make_tarfile(output_filename="pmc_json.tar.gz", work_cmd=staging_folder + "/document_parses/", source_dir="pmc_json")

    # Upload new RAW JSONs tar to S3
    print("Upload TAR Raw JSONs into S3")
    Conf.s3_utils.upload_file(file=staging_folder + "/document_parses/pdf_json.tar.gz", bucket="advana-data-zone",
                              object_prefix="bronze/gamechanger/projects/" + gc_project + "/raw_jsons/")
    Conf.s3_utils.upload_file(file=staging_folder + "/document_parses/pmc_json.tar.gz", bucket="advana-data-zone",
                              object_prefix="bronze/gamechanger/projects/" + gc_project + "/raw_jsons/")


    end = time()
    print(f'Total time -- It took {end - start} seconds!')

    print("DONE!!!!!!")


# Extract tar file  Raw covid_19 from website
def extract_cord_19_raw_file(raw_cord_file: Union[str, Path], tmp_folder: Union[str, Path]):
    local_cord_dir_path = Path(raw_cord_file).resolve()
    local_tmp_path = Path(tmp_folder).resolve()
    if not tarfile.is_tarfile(local_cord_dir_path):
        raise Exception("Not a tar.gz file")

    with tarfile.open(local_cord_dir_path, "r:gz") as archive:
        archive.list(verbose=True)
        archive.extractall(local_tmp_path)

        for file in os.listdir(str(local_tmp_path.absolute()) + "/" + os.path.commonprefix(archive.getnames())):
            if "document_parses.tar.gz" == file:
                local_doc_files = Path(str(local_tmp_path.absolute()) + "/" + os.path.commonprefix(
                    archive.getnames()) + "document_parses.tar.gz").resolve()
                with tarfile.open(local_doc_files) as archive_docs:
                    archive_docs.extractall(local_tmp_path)
            elif "metadata.csv" == file:
                local_metadata_path = Path(str(local_tmp_path.absolute()) + "/" + os.path.commonprefix(
                    archive.getnames()) + "metadata.csv").resolve()
                copyfile(str(local_metadata_path), str(local_tmp_path) + "/" + "metadata.csv")

        shutil.rmtree(str(local_tmp_path.absolute()) + "/" + os.path.commonprefix(archive.getnames()),
                      ignore_errors=True)


def create_diff(old_files: Union[str, Path], new_files: Union[str, Path], staging_folder: Union[str, Path],
                folder_name: str):
    dc = filecmp.dircmp(old_files, new_files)

    if not os.path.exists(staging_folder + "/modification/"):
        os.makedirs(staging_folder + "/modification/")

    if not os.path.exists(staging_folder + "/modification/" + folder_name + "/"):
        os.makedirs(staging_folder + "/modification/" + folder_name + "/")

    if not os.path.exists(staging_folder + "/modification/" + folder_name + "/"):
        os.makedirs(staging_folder + "/modification/" + folder_name + "/")

    print("Left only Files (old): ")
    for left_only in dc.left_only:
        # print(left_only)
        with open(staging_folder + "/modification/" + "files_to_remove.txt", 'a') as remove_files:
            if left_only.endswith(".json"):
                remove_files.write(left_only)
                remove_files.write('\n')

    print("Right only Files (new): ")
    for right_only in dc.right_only:
        copyfile(new_files + "/" + right_only, staging_folder + "/modification/" + folder_name + "/" + right_only)

    print("Diff Files: ")
    for diff in dc.diff_files:
        copyfile(new_files + "/" + diff, staging_folder + "/modification/" + folder_name + "/" + diff)


def run_pdf_generator(staging_folder: Union[str, Path], input_raw_jsons_dir: Union[Path, str],
                      metadata_file: Union[Path, str],
                      output_pdf_dir: Union[Path, str], ignore_files: Union[Path, str], multiprocess: int):
    input_raw_jsons_dir_path = Path(input_raw_jsons_dir).resolve()
    output_pdf_dir_path = Path(output_pdf_dir).resolve()
    metadata_file_path = Path(metadata_file).resolve()
    ignore_file_path = Path(ignore_files).resolve()
    staging_folder_path = Path(staging_folder).resolve()

    if not os.path.exists(str(staging_folder_path) + "/modification/pdf/"):
        os.makedirs(str(staging_folder_path) + "/modification/pdf/")

    COVIDDocument.process_dir(dir_path=str(input_raw_jsons_dir_path), out_dir=str(output_pdf_dir_path),
                              metadata_file=str(metadata_file_path), ignore_files=str(ignore_file_path),
                              multiprocess=str(multiprocess))


def run_docparser(staging_folder: Union[str, Path], input_dir: Union[Path, str],
                  output_dir: Union[Path, str],
                  multiprocess: int):
    input_dir_path = Path(input_dir).resolve()
    output_dir_path = Path(output_dir).resolve()
    staging_folder_path = Path(staging_folder).resolve()

    if not os.path.exists(str(staging_folder_path) + "/modification/json/"):
        os.makedirs(str(staging_folder_path) + "/modification/json/")

    Document.process_dir(
        dir_path=str(input_dir_path),
        out_dir=str(output_dir_path),
        clean=False,
        meta_data=str(input_dir_path),
        multiprocess=str(multiprocess),
        skip_optional_ds=True
    )


def run_indexer(index_name: str, alias: str, ingest_dir):
    ingest_dir_path = Path(ingest_dir).resolve()

    publisher = ConfiguredElasticsearchPublisher(index_name=str(index_name), ingest_dir=str(ingest_dir_path),
                                                 alias=str(alias))

    publisher.create_index()
    publisher.index_jsons()
    if alias:
        publisher.update_alias()


def make_tarfile(output_filename, work_cmd, source_dir):
    # Python is such a slow language. we really should run tar from a subprocess instead of python code.
    sub.run(['tar', '-czvf', output_filename, source_dir], cwd=work_cmd, check=True)
    # with tarfile.open(output_filename, "w:gz") as tar:
    #     tar.add(source_dir, arcname=os.path.basename(source_dir))


def delete_file_no_longer_need_in_s3(files_to_remove: Union[str, Path], gc_project: str):
    if Path(files_to_remove).exists():
        files_to_remove_path = Path(files_to_remove).resolve()
        # Delete Generated file no longer in the COVID dataset - Generated JSONs
        with open(files_to_remove_path, 'r') as remove_file:
            line = remove_file.readline()
            cnt = 1
            while line:
                filename = re.sub('.xml.json|.json', '', line)

                Conf.s3_utils.delete_object(object_path="bronze/gamechanger/projects/" + gc_project + "/json/" + line.strip(),
                                            bucket="advana-data-zone")
                Conf.s3_utils.delete_object(
                    object_path="bronze/gamechanger/projects/" + gc_project + "/pdf/" + filename.strip() + ".pdf",
                    bucket="advana-data-zone")
                Conf.s3_utils.delete_object(
                    object_path="bronze/gamechanger/projects/" + gc_project + "/pdf/" + filename.strip() + ".pdf.metadata",
                    bucket="advana-data-zone")

                print("deleted {}: {}".format(cnt, filename.strip()))
                line = remove_file.readline()
                cnt += 1


def delete_records_in_elasticsearch(file_list_records: Union[str, Path], index_name: str, alias: str,  ingest_dir):
    es_client = ConfiguredElasticsearchPublisher(ingest_dir=ingest_dir, index_name=index_name, alias=alias)
    if Path(file_list_records).exists():
        files_to_remove_path = Path(file_list_records).resolve()
        # Delete Generated file no longer in the COVID dataset - Elasticsearch
        records = list()
        with open(files_to_remove_path, 'r') as remove_file:
            line = remove_file.readline()
            while line:
                records.append(line)
                line = remove_file.readline()

        es_client.delete_record(records)


if __name__ == '__main__':
    run()
