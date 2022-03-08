import time
import click
import json
import os
import concurrent.futures
import traceback
import subprocess

from typing import Union
from pathlib import Path
from urllib3.exceptions import ProtocolError

from dataPipelines.gc_eda_pipeline.conf import Conf
from dataPipelines.gc_eda_pipeline.metadata.generate_metadata import generate_metadata_data
from dataPipelines.gc_eda_pipeline.doc_extractor.doc_extractor import ocr_process, extract_text
from dataPipelines.gc_eda_pipeline.utils.eda_utils import read_extension_conf
from dataPipelines.gc_eda_pipeline.indexer.indexer import index_data_file, create_index
from dataPipelines.gc_eda_pipeline.utils.eda_job_type import EDAJobType
from dataPipelines.gc_eda_pipeline.database.database import audit_file_exist, audit_get_record, audit_failed_record
from dataPipelines.gc_eda_pipeline.database.database import audit_success_record, audit_get_failed_record


@click.command()
@click.option(
    '-s',
    '--staging-folder',
    help="A temp folder for which the eda data will be staged for processing.",
    required=True,
    type=str,
)
@click.option(
    '--aws-s3-input-pdf-prefix',
    help="""The S3 Prefix for processing data, For multi Prefix the follow is  
            piee/unarchive_pdf/edapdf_315/,piee/unarchive_pdf/edapdf_314/,piee/unarchive_pdf/edapdf_313/
        """,
    required=False,
    type=str
)
@click.option(
    '-p',
    '--workers-ocr',
    required=False,
    default=-1,
    type=int,
    help="Multiprocessing. If treated like flag, will do max cores available. \
                if treated like option will take integer for number of cores.",
)
@click.option(
    '--max-workers',
    required=False,
    default=-1,
    type=int,
    help="Multiprocessing. If treated like flag, will do max cores available. \
                if treated like option will take integer for number of cores.",
)
@click.option(
    '--eda-job-type',
    type=click.Choice([e.value for e in EDAJobType]),
    help="""Determines how the data should be processed,
         """,
    default=EDAJobType.NORMAL.value
)
@click.option(
    '--loop-number',
    help="You should not need to change this value",
    required=False,
    type=int,
    default=50000
)
#TODO update the UUID for ES for doc
def run(staging_folder: str, aws_s3_input_pdf_prefix: str, max_workers: int, workers_ocr: int, eda_job_type: str,
        loop_number: int):

    ingestion(staging_folder=staging_folder, aws_s3_input_pdf_prefix=aws_s3_input_pdf_prefix, max_workers=max_workers,
              eda_job_type=eda_job_type, workers_ocr=workers_ocr, loop_number=loop_number)


def ingestion(staging_folder: str, aws_s3_input_pdf_prefix: str, max_workers: int, workers_ocr: int, eda_job_type: str,
              loop_number: int):
    print("Starting Gamechanger EDA Symphony Pipeline")
    os.environ["AWS_METADATA_SERVICE_TIMEOUT"] = "20"
    os.environ["AWS_METADATA_SERVICE_NUM_ATTEMPTS"] = "40"

    start_app = time.time()
    # Load Extensions configuration files.
    data_conf_filter = read_extension_conf()

    aws_s3_output_pdf_prefix = data_conf_filter['eda']['aws_s3_output_pdf_prefix']
    aws_s3_json_prefix = data_conf_filter['eda']['aws_s3_json_prefix']

    # Create EDA index
    print(f"EDA Index {data_conf_filter['eda']['eda_index']}")
    create_index(index_name=data_conf_filter['eda']['eda_index'], alias=data_conf_filter['eda']['eda_index_alias'])

    for input_loc in aws_s3_input_pdf_prefix.split(","):
        print(f"Processing Directory {input_loc}")
        start = time.time()
        process_type = EDAJobType(eda_job_type)

        # Get list of files from S3
        start_file_list = time.time()
        file_list = list_of_to_process(staging_folder, input_loc)
        end_file_list = time.time()
        total_num_files = len(file_list)
        number_file_processed = 0
        number_file_failed = 0
        percentage_completed = 5

        # How many elements each list should have # work around with issue on queue being over filled
        n = loop_number
        # using list comprehension
        process_list = [file_list[i * n:(i + 1) * n] for i in range((len(file_list) + n - 1) // n)]

        for item_process in process_list:
            with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
                results = [executor.submit(process_doc, file, staging_folder, data_conf_filter, workers_ocr,
                                           aws_s3_output_pdf_prefix, aws_s3_json_prefix, process_type)
                           for file in item_process]
                count = 0
                none_type = type(None)
                for fut in concurrent.futures.as_completed(results):
                    if not isinstance(fut, none_type):
                        try:
                            if fut.result() is not None:
                                status = fut.result().get('status')
                                if "already_processed" == status:
                                    print(f"Following file {fut.result().get('filename')} was already processed, extra info: "
                                        f"{fut.result().get('info')}")
                                    number_file_processed = number_file_processed + 1
                                elif "completed" == status:
                                    print(f"Following file {fut.result().get('filename')} was processed, extra info: "
                                          f"{fut.result().get('info')}")
                                    number_file_processed = number_file_processed + 1
                                elif "failed" == status:
                                    print(f"Following file {fut.result().get('filename')} failed, extra info: "
                                          f"{fut.result().get('info')}")
                                    number_file_failed = number_file_failed + 1
                                elif "skip" == status:
                                    print(f"Following file {fut.result().get('filename')} was skipped, extra info: "
                                          f"{fut.result().get('info')}")
                                count = count + 1

                            if (count / total_num_files * 100) > percentage_completed:
                                percentage_completed = percentage_completed + 5
                                print(f"Processed so far {round(count / total_num_files * 100, 2)}%")
                        except Exception as exc:
                            value = str(exc)
                            if value == "not a PDF":
                                print("EDA ****  File is not a PDF **** EDA")
                            else:
                                print(f"EDA **** Failed to process '{exc}'  ****  EDA")
                                traceback.print_exc()
                            number_file_failed = number_file_failed + 1
                    else:
                        print("EDA ****  File is not a PDF **** EDA")

        # Index Files into Elasticsearch
        start_bulk_index = time.time()
        eda_publisher = create_index(index_name=data_conf_filter['eda']['eda_index'],
                                     alias=data_conf_filter['eda']['eda_index_alias'],
                                     ingest_dir=staging_folder + "/index/" + input_loc + "/")
        eda_publisher.index_jsons()
        end_bulk_index = time.time()
        end = time.time()

        delete_index_folder_content = staging_folder + "/index/" + input_loc + "/"
        delete_pdf_folder_content = staging_folder + "/pdf/" + input_loc + "/"
        delete_json_folder_content = staging_folder + "/json/" + input_loc + "/"
        subprocess.call(f'rm -rf {delete_index_folder_content}', shell=True)
        subprocess.call(f'rm -rf {delete_pdf_folder_content}', shell=True)
        subprocess.call(f'rm -rf {delete_json_folder_content}', shell=True)

        print("-----------  Process Status -----------")
        print(f"Dataset {input_loc}")
        print(f"Number files Processed {number_file_processed}")
        print(f"Number files Failed {number_file_failed}")
        print(f"Time to generate file list from S3 {round(end_file_list - start_file_list, 2)} secs")
        print(f"Time to index into Elasticsearch: {round(float(end_bulk_index - start_bulk_index), 2)}")
        print(f"Index rate {round(number_file_processed/(end_bulk_index - start_bulk_index), 2)} files/sec")
        print(f"Process file rate {round(number_file_processed / (end - start), 2)} files/sec)")
        print(f'Total time -- It took {round(end - start, 2)} seconds!')
        print("--------------------------------------")

    print("DONE!!!!!!")
    end_app = time.time()
    print(f'Total APP time -- It took {end_app - start_app} seconds!')


def process_doc(file: str, staging_folder: Union[str, Path], data_conf_filter: dict, multiprocess: int,
                aws_s3_output_pdf_prefix: str, aws_s3_json_prefix: str,
                process_type: EDAJobType):
    os.environ["AWS_METADATA_SERVICE_TIMEOUT"] = "20"
    os.environ["AWS_METADATA_SERVICE_NUM_ATTEMPTS"] = "40"

    path, filename = os.path.split(file)
    filename_without_ext, file_extension = os.path.splitext(filename)

    # Get connections to the Elasticsearch for the audit and eda indexes
    audit_rec = {"filename": filename, "eda_path": file, "base_path": path, "gc_path": "", "json_path": "",
                 "metadata_type": "none", "is_metadata_suc": False, "is_ocr": False, "modified_date_dt": 0}

    # Determine if we want to process this record
    # Make sure the file is a PDF file.
    if file_extension != ".pdf":
        failed_data = {"filename": filename, "base_path": path, "reason": "File is not pdf",
                       "modified_date_dt": int(time.time())}
        audit_list = [failed_data]
        audit_failed_record(data=audit_list)
        return {'filename': filename, "status": "failed", "info": "File does not have a pdf extension"}

    # Check to see if the file as been processed before
    is_process_already = audit_file_exist(filename)

    update_metadata = False
    process_file = False

    # Determine how/or if the file need to be processed
    if EDAJobType(process_type) == EDAJobType.NORMAL:
        if is_process_already:
            record = audit_get_record(filename=filename)
            successfully_filename = record.get('filename')
            successfully_eda_path = record.get('eda_path')
            if successfully_filename:
                if filename == successfully_filename and file == successfully_eda_path:
                    return {'filename': filename, "status": "already_processed"}
                elif filename == successfully_filename and file != successfully_eda_path:
                    failed_data = {"filename": filename, "base_path": path, "reason": "File is a dup",
                                   "modified_date_dt": int(time.time())}
                    audit_list = [failed_data]
                    audit_failed_record(data=audit_list)
                    return {'filename': filename, "status": "already_processed or a dup file"}
            else:
                process_file = True
        else:
            failed_record = audit_get_failed_record(filename=filename, base_path=path)
            if failed_record:
                process_file = False
            else:
                process_file = True
    elif EDAJobType(process_type) == EDAJobType.REINDEX:
        record = audit_get_record(filename=filename)
        if record is None:
            return {'filename': filename, "status": "Was never index. skipping"}
        if record is not None:
            audit_filename = record.get('filename')
            audit_base_path = record.get('base_path')
            if audit_filename == filename and audit_base_path == path:
                audit_rec.update({'json_path': record.get('json_path'), 'gc_path': record.get('gc_path')})
                process_file = False
                update_metadata = True
            else:
                return {'filename': filename, "status": "Was never index. skipping"}
        else:
            process_file = False
            update_metadata = False
    elif EDAJobType(process_type) == EDAJobType.REPROCESS:
        if is_process_already:
            record = audit_get_record(filename=filename)
            successfully_filename = record.get('filename')
            successfully_eda_path = record.get('eda_path')
            if successfully_filename:
                if filename == successfully_filename and file == successfully_eda_path:
                    process_file = True
                elif filename == successfully_filename and file != successfully_eda_path:
                    failed_data = {"filename": filename, "base_path": path, "reason": "File is a dup",
                                   "modified_date_dt": int(time.time())}
                    audit_list = [failed_data]
                    audit_failed_record(data=audit_list)
                    return {'filename': filename, "status": "already_processed or a dup file"}
            else:
                process_file = True
        else:
            failed_record = audit_get_failed_record(filename=filename, base_path=path)
            if failed_record:
                process_file = False
            else:
                process_file = True

    # Process the file
    if update_metadata:  # re-index
        error_count = 0
        index_json_created = False
        fail = False

        while not index_json_created and not fail:
            try:
                # Get Doc Parsed json
                ex_file_s3_path = aws_s3_json_prefix + "/" + path + "/" + filename_without_ext + ".json"
                index_file_local_path = path + "/" + filename_without_ext + ".json"
                if Conf.s3_utils.prefix_exists(prefix_path=ex_file_s3_path):
                    raw_docparser_data = json.loads(Conf.s3_utils.object_content(object_path=ex_file_s3_path))

                    md_data = generate_metadata_data(data_conf_filter=data_conf_filter,
                                                     file=file, filename=filename,
                                                     aws_s3_output_pdf_prefix=aws_s3_output_pdf_prefix,
                                                     audit_rec=audit_rec)

                    index_data_file(staging_folder=staging_folder, metadata_file_data=md_data,
                                    parsed_pdf_file_data=raw_docparser_data, ex_file_s3_path=ex_file_s3_path,
                                    audit_rec=audit_rec, index_file_local_path=index_file_local_path)

                    audit_list = [audit_rec]
                    audit_success_record(data=audit_list)

                    return {'filename': filename, "status": "completed", "info": "update-metadata"}
                else:
                    failed_data = {"filename": filename, "base_path": path, "reason": "File might be corrupted",
                                   "modified_date_dt": int(time.time())}
                    audit_list = [failed_data]
                    audit_failed_record(data=audit_list)

                    return {'filename': filename, "status": "failed", "info": "unable to file docfile " +
                                                                              ex_file_s3_path + " file"}
            except (ProtocolError, ConnectionError) as e:
                error_count += 1
                time.sleep(1)
            finally:
                if error_count > 10:
                    print(f"Tried to get generate index json for file {filename}")
                    return {'filename': filename, "status": "failed", "info": "unable to create index file"}

        return {'filename': filename, "status": "completed", "info": "update-metadata"}
    elif process_file:  # File has never been process or we want to re-process the file
        files_delete = []

        # Generate metadata file
        md_data = generate_metadata_data(data_conf_filter=data_conf_filter,
                                         file=file, filename=filename,
                                         aws_s3_output_pdf_prefix=aws_s3_output_pdf_prefix,
                                         audit_rec=audit_rec)

        # Download PDF file/OCR PDF if need
        is_pdf_file, pdf_file_local_path, pdf_file_s3_path = ocr_process(staging_folder=staging_folder, file=file,
                                                                         multiprocess=multiprocess,
                                                                         aws_s3_output_pdf_prefix=aws_s3_output_pdf_prefix,
                                                                         audit_rec=audit_rec)
        files_delete.append(pdf_file_local_path)
        # Doc Parser/ Extract Text
        if is_pdf_file and os.path.exists(pdf_file_local_path):
            ex_file_local_path, ex_file_s3_path, is_extract_suc = extract_text(staging_folder=staging_folder,
                                                                               path=path,
                                                                               pdf_file_local_path=pdf_file_local_path,
                                                                               filename_without_ext=filename_without_ext,
                                                                               aws_s3_json_prefix=aws_s3_json_prefix,
                                                                               audit_rec=audit_rec)
            files_delete.append(pdf_file_local_path)
            if is_extract_suc:
                # Index into Elasticsearch
                with open(ex_file_local_path) as docparser_file:
                    raw_docparser_data = json.load(docparser_file)

                index_file_local_path = path + "/" + filename_without_ext + ".json"

                index_data_file(staging_folder=staging_folder, metadata_file_data=md_data,
                                parsed_pdf_file_data=raw_docparser_data, ex_file_s3_path=ex_file_s3_path,
                                audit_rec=audit_rec, index_file_local_path=index_file_local_path)

                # Delete for local file system to free up space.
                cleanup_record(files_delete)
                audit_list = [audit_rec]
                audit_success_record(data=audit_list)
                return {'filename': filename, "status": "completed", "info": "new record"}
            else:
                # Delete for local file system to free up space.
                cleanup_record(files_delete)
                failed_data = {"filename": filename, "base_path": path, "reason": "File might be corrupted",
                               "modified_date_dt": int(time.time())}
                audit_list = [failed_data]
                audit_failed_record(data=audit_list)
                return {'filename': filename, "status": "failed", "info": "Not a PDF file"}

    failed_data = {"filename": filename, "base_path": path, "reason": "File might be corrupted", "modified_date_dt": int(time.time())}
    audit_list = [failed_data]
    audit_failed_record(data=audit_list)
    return {'filename': filename, "status": "failed", "info": "File might be corrupted"}


def generate_list_pdf_download(metadata_dir: Union[str, Path]) -> list:
    metadata_dir_path = Path(metadata_dir).resolve()
    file_list = []
    for filename in os.listdir(metadata_dir_path):
        if filename.endswith(".pdf.metadata"):
            with open(str(metadata_dir_path) + "/" + filename) as metadata_file:
                data = json.load(metadata_file)
                if 'extensions' in data:
                    extensions = data['extensions']
                    if 'pdf_filename_eda_ext' in extensions:
                        file_list.append(extensions['pdf_filename_eda_ext'])
    return file_list


def list_of_to_process(staging_folder: Union[str, Path], aws_s3_input_pdf_prefix: str) -> list:
    files = []
    for obj_path in Conf.s3_utils.iter_object_paths_at_prefix(prefix=aws_s3_input_pdf_prefix):
        path, filename = os.path.split(obj_path)
        if filename != "":
            files.append(obj_path)
            if not os.path.exists(staging_folder + "/pdf/" + path + "/"):
                os.makedirs(staging_folder + "/pdf/" + path + "/")
            if not os.path.exists(staging_folder + "/json/" + path + "/"):
                os.makedirs(staging_folder + "/json/" + path + "/")
            if not os.path.exists(staging_folder + "/index/" + path + "/"):
                os.makedirs(staging_folder + "/index/" + path + "/")
    return files


def cleanup_record(delete_files: list):
    for delete_file in delete_files:
        if os.path.exists(delete_file):
            os.remove(delete_file)


if __name__ == '__main__':
    run()
