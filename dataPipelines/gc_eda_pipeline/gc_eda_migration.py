import time
import click
import os
from tqdm import tqdm
import concurrent.futures
from dataPipelines.gc_eda_pipeline.conf import Conf
from dataPipelines.gc_eda_pipeline.database.connection import ConnectionPool
from dataPipelines.gc_eda_pipeline.utils.eda_utils import read_extension_conf


@click.command()
@click.option(
    '--aws-s3-input-json-prefix',
    required=False,
    type=str
)
@click.option(
    '-p',
    '--number-of-datasets-to-process-at-time',
    required=False,
    default=1,
    help="The number of datasets to process at time. Locally should be set to 1-5, prod/dev should be around 250",
    type=int
)
@click.option(
    '-t',
    '--number-threads-per-dataset',
    required=False,
    default=1,
    type=int,
    help="Number of threads to run within a dataset. Locally should be set to 1-20, prod/dev should be around 250",
)
def run(aws_s3_input_json_prefix: str, number_of_datasets_to_process_at_time: int, number_threads_per_dataset: int):
    start = time.time()
    print("Starting Gamechanger Migration Symphony Pipeline")

    # Load Extensions configuration files.
    data_conf_filter = read_extension_conf()
    aws_s3_json_prefix = data_conf_filter['eda']['aws_s3_json_prefix']

    with concurrent.futures.ProcessPoolExecutor(max_workers=number_of_datasets_to_process_at_time) as executor:
        results = [executor.submit(migration_dir_task, input_loc, aws_s3_json_prefix, number_threads_per_dataset)
                   for input_loc in aws_s3_input_json_prefix.split(",")]
        none_type = type(None)
        for fut in concurrent.futures.as_completed(results):
            if not isinstance(fut, none_type):
                try:
                    if fut.result() is not None:
                        print(fut.result())
                except Exception as exc:
                    value = str(exc)
                    print(value)
            else:
                print("Somethting went really wrong")
        executor.shutdown(wait=True)

    end = time.time()
    print("-----------  Process Status -----------")
    print(f'Total time -- It took {round(end - start, 2)} seconds!')
    print("--------------------------------------")


def migration_dir_task(input_loc: str, aws_s3_json_prefix: str,  number_threads_per_dataset: int):
    print(f"Processing Directory {input_loc}")
    start = time.time()

    with concurrent.futures.ThreadPoolExecutor(max_workers=number_threads_per_dataset) as executor:
        results = [executor.submit(process_record, json_path, aws_s3_json_prefix) for json_path in s3_obj_paths(input_loc)]

        none_type = type(None)
        for fut in concurrent.futures.as_completed(results):
            if not isinstance(fut, none_type):
                try:
                    if fut.result() is not None:
                        print(fut.result())
                except Exception as exc:
                    value = str(exc)
                    print(value)
            else:
                print("Somethting went really wrong")
        executor.shutdown(wait=True)
    end = time.time()
    print("-----------  Process Status -----------")
    print(f"Dataset {input_loc}")
    print(f'Time -- It took {round(end - start, 2)} seconds!')
    print("--------------------------------------")


def process_record(json_path, aws_s3_json_prefix):
    path, filename_json = os.path.split(json_path)

    data_conf_filter = read_extension_conf()
    audit_db = ConnectionPool(db_hostname=data_conf_filter['eda']['database']['hostname'],
                              db_port_number=data_conf_filter['eda']['database']['port'],
                              db_user_name=data_conf_filter['eda']['database']['user'],
                              db_password=data_conf_filter['eda']['database']['password'],
                              db_dbname=data_conf_filter['eda']['database']['db'],
                              multithreading=True, minconn=1, maxconn=3)

    filename = filename_json.replace('.json', '.pdf')
    eda_path = json_path.replace(aws_s3_json_prefix, '').lstrip("/").replace('.json', '.pdf')
    base_path = json_path.replace(aws_s3_json_prefix, '').lstrip("/").replace(filename_json, '').rstrip("/")
    gc_path = json_path.replace("/json/", "/pdf/").replace('.json', '.pdf')

    # Check if file is a dup.
    # Check to see if the file as been processed before
    is_process_filename, is_process_base_path = audit_db.audit_is_processed(filename)
    if is_process_filename:
        if is_process_base_path != base_path:
            failed_data = {"filename": filename, "base_path": path, "reason": "File is duplication",
                           "modified_date_dt": int(time.time())}
            audit_list = [failed_data]
            audit_db.audit_failed_record(data=audit_list)
    else:
        audit_rec = {"filename": filename, "eda_path": eda_path, "base_path": base_path, "gc_path": gc_path,
                     "json_path": json_path, "is_ocr": None, "is_pds": False, "is_syn": False, "is_fpds_ng": False,
                     "is_elasticsearch": False, "is_supplementary_file_missing": False,
                     "modified_date_dt": int(time.time())}
        audit_list = [audit_rec]
        audit_db.audit_success_record(data=audit_list)


def s3_obj_paths(aws_s3_input_json_prefix: str) -> list:
    os.environ["AWS_METADATA_SERVICE_TIMEOUT"] = "20"
    os.environ["AWS_METADATA_SERVICE_NUM_ATTEMPTS"] = "40"
    print(type(Conf.ch.s3_client))   # Issue if this is not call before using s3 command in threads.
    for obj_path in Conf.s3_utils.iter_object_paths_at_prefix(prefix=aws_s3_input_json_prefix):
        path, filename = os.path.split(obj_path)
        filename_without_ext, file_extension = os.path.splitext(filename)
        if file_extension == ".json":
            yield obj_path


if __name__ == '__main__':
    run()
