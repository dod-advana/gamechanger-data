import time
import click
import os
import concurrent.futures
import traceback
import subprocess

from tqdm import tqdm
from typing import Union
from pathlib import Path
from dataPipelines.gc_eda_pipeline.conf import Conf
from dataPipelines.gc_eda_pipeline.utils.eda_utils import read_extension_conf
from dataPipelines.gc_eda_pipeline.database.connection import ConnectionPool
from dataPipelines.gc_eda_pipeline.doc_extractor.doc_extractor import ocr_process, extract_text

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
    '--loop-number',
    help="You should not need to change this value",
    required=False,
    type=int,
    default=50000
)
def run(staging_folder: str, aws_s3_input_pdf_prefix: str, max_workers: int, workers_ocr: int,  loop_number: int):
    ingestion(staging_folder=staging_folder, aws_s3_input_pdf_prefix=aws_s3_input_pdf_prefix, max_workers=max_workers,
              workers_ocr=workers_ocr, loop_number=loop_number)


def ingestion(staging_folder: str, aws_s3_input_pdf_prefix: str, max_workers: int, workers_ocr: int, loop_number: int):
    print("Starting Gamechanger EDA Symphony Pipeline")
    os.environ["AWS_METADATA_SERVICE_TIMEOUT"] = "20"
    os.environ["AWS_METADATA_SERVICE_NUM_ATTEMPTS"] = "40"

    start_app = time.time()

    # Load Extensions configuration files.
    data_conf_filter = read_extension_conf()

    aws_s3_output_pdf_prefix = data_conf_filter['eda']['aws_s3_output_pdf_prefix']
    aws_s3_json_prefix = data_conf_filter['eda']['aws_s3_json_prefix']

    for input_loc in aws_s3_input_pdf_prefix.split(","):
        print(f"Processing Directory {input_loc}")
        start = time.time()

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
                                           aws_s3_output_pdf_prefix, aws_s3_json_prefix) for file in tqdm(item_process)]
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
                                    # print(f"Following file {fut.result().get('filename')} was processed, extra info: "
                                    #       f"{fut.result().get('info')}")
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
                                print(f"Processed so far {round(count / total_num_files * 100, 2)}% for {input_loc}")
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

        delete_pdf_folder_content = staging_folder + "/pdf/" + input_loc + "/"
        delete_json_folder_content = staging_folder + "/json/" + input_loc + "/"
        subprocess.call(f'rm -rf {delete_pdf_folder_content}', shell=True)
        subprocess.call(f'rm -rf {delete_json_folder_content}', shell=True)

        end = time.time()

        print("-----------  Process Status -----------")
        print(f"Dataset {input_loc}")
        print(f"Number files Processed {number_file_processed}")
        print(f"Number files Failed {number_file_failed}")
        print(f"Time to generate file list from S3 {round(end_file_list - start_file_list, 2)} secs")
        print(f"Process file rate {round(number_file_processed / (end - start), 2)} files/sec)")
        print(f'Total time -- It took {round(end - start, 2)} seconds!')
        print("--------------------------------------")

    print("DONE!!!!!!")
    end_app = time.time()
    print(f'Total APP time -- It took {end_app - start_app} seconds!')


def process_doc(file: str, staging_folder: Union[str, Path], data_conf_filter: dict, multiprocess: int,
                aws_s3_output_pdf_prefix: str, aws_s3_json_prefix: str):
    os.environ["AWS_METADATA_SERVICE_TIMEOUT"] = "20"
    os.environ["AWS_METADATA_SERVICE_NUM_ATTEMPTS"] = "40"
    files_delete = []

    data_conf_filter = read_extension_conf()
    db_pool = ConnectionPool(db_hostname=data_conf_filter['eda']['database']['hostname'],
                             db_port_number=data_conf_filter['eda']['database']['port'],
                             db_user_name=data_conf_filter['eda']['database']['user'],
                             db_password=data_conf_filter['eda']['database']['password'],
                             db_dbname=data_conf_filter['eda']['database']['db'], multithreading=True, maxconn=500)

    path, filename = os.path.split(file)
    filename_without_ext, file_extension = os.path.splitext(filename)

    audit_rec = {"filename": filename, "eda_path": file, "base_path": path, "gc_path": "", "json_path": "",
                 "is_ocr": False, "is_pds": False, "is_syn": False, "is_fpds_ng": False, "is_elasticsearch": False,
                 "is_supplementary_file_missing": False, "modified_date_dt": 0}

    # Determine if we want to process this record
    # Make sure the file is a PDF file.
    if file_extension != ".pdf":
        failed_data = {"filename": filename, "base_path": path, "reason": "File is not pdf",
                       "modified_date_dt": int(time.time())}
        audit_list = [failed_data]
        db_pool.audit_failed_record(data=audit_list)
        return {'filename': filename, "status": "failed", "info": "File does not have a pdf extension"}

    # Check if file is a dup.
    # Check to see if the file as been processed before
    is_process_filename, is_process_base_path = db_pool.audit_is_processed(filename)
    if is_process_filename:
        if is_process_base_path != path:
            failed_data = {"filename": filename, "base_path": path, "reason": "File is duplication",
                           "modified_date_dt": int(time.time())}
            audit_list = [failed_data]
            db_pool.audit_failed_record(data=audit_list)
            return {'filename': filename, "status": "already_processed", "info": "File is duplication"}

    # Download PDF file/OCR PDF if need be
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

            # Delete for local file system to free up space.
            cleanup_record(files_delete)
            audit_list = [audit_rec]
            db_pool.audit_success_record(data=audit_list)
            return {'filename': filename, "status": "completed", "info": "new record"}
        else:
            # Delete for local file system to free up space.
            cleanup_record(files_delete)
            failed_data = {"filename": filename, "base_path": path, "reason": "File might be corrupted",
                           "modified_date_dt": int(time.time())}
            audit_list = [failed_data]
            db_pool.audit_failed_record(data=audit_list)
            return {'filename': filename, "status": "failed", "info": "Not a PDF file"}

    failed_data = {"filename": filename, "base_path": path, "reason": "File might be corrupted",
                   "modified_date_dt": int(time.time())}

    audit_list = [failed_data]
    db_pool.audit_failed_record(data=audit_list)
    return {'filename': filename, "status": "failed", "info": "File might be corrupted"}


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
    return files


def cleanup_record(delete_files: list):
    for delete_file in delete_files:
        if os.path.exists(delete_file):
            os.remove(delete_file)


if __name__ == '__main__':
    run()

