import time
from time import sleep, perf_counter
import click
import os
from tqdm import tqdm
from threading import Thread

from dataPipelines.gc_eda_pipeline.conf import Conf
from dataPipelines.gc_eda_pipeline.utils.eda_utils import read_extension_conf
from dataPipelines.gc_eda_pipeline.database.database import audit_file_exist, audit_success_record, audit_failed_record


@click.command()
@click.option(
    '--aws-s3-input-json-prefix',
    required=False,
    type=str
)
def run(aws_s3_input_json_prefix: str):
    start = time.time()
    print("Starting Gamechanger Migration Symphony Pipeline")
    os.environ["AWS_METADATA_SERVICE_TIMEOUT"] = "20"
    os.environ["AWS_METADATA_SERVICE_NUM_ATTEMPTS"] = "40"

    # Load Extensions configuration files.
    data_conf_filter = read_extension_conf()

    aws_s3_json_prefix = data_conf_filter['eda']['aws_s3_json_prefix']

    for input_loc in aws_s3_input_json_prefix.split(","):
        t = Thread(target=migration_dir_task, args=(input_loc, aws_s3_json_prefix, ))
        threads.append(t)
        t.start()
        # print(f"Processing Directory {input_loc}")
        # start = time.time()
        #
        # for json_path in tqdm(s3_obj_paths(input_loc)):
        #     path, filename_json = os.path.split(json_path)
        #
        #     filename = filename_json.replace('.json', '.pdf')
        #     eda_path = json_path.replace(aws_s3_json_prefix, '').lstrip("/").replace('.json', '.pdf')
        #     base_path = json_path.replace(aws_s3_json_prefix, '').lstrip("/").replace(filename_json, '').rstrip("/")
        #     gc_path = json_path.replace("/json/", "/pdf/").replace('.json', '.pdf')
        #
        #     # Check if file is a dup.
        #     # Check to see if the file as been processed before
        #     is_process_already = audit_file_exist(filename, path)
        #     if is_process_already:
        #         failed_data = {"filename": filename, "base_path": path, "reason": "File is duplication",
        #                        "modified_date_dt": int(time.time())}
        #         audit_list = [failed_data]
        #         audit_failed_record(data=audit_list)
        #         continue
        #
        #     audit_rec = {"filename": filename, "eda_path": eda_path, "base_path": base_path, "gc_path": gc_path,
        #                  "json_path": json_path, "is_ocr": None, "is_pds": False, "is_syn": False, "is_fpds_ng": False,
        #                  "is_elasticsearch": False, "is_supplementary_file_missing": False, "modified_date_dt": 0}
        #
        #     audit_list = [audit_rec]
        #     audit_success_record(data=audit_list)

    end = time.time()
    print("-----------  Process Status -----------")
    print(f'Total time -- It took {round(end - start, 2)} seconds!')
    print("--------------------------------------")


def migration_dir_task(input_loc: str, aws_s3_json_prefix: str):
    print(f"Processing Directory {input_loc}")
    start = time.time()

    for json_path in tqdm(s3_obj_paths(input_loc)):
        path, filename_json = os.path.split(json_path)

        filename = filename_json.replace('.json', '.pdf')
        eda_path = json_path.replace(aws_s3_json_prefix, '').lstrip("/").replace('.json', '.pdf')
        base_path = json_path.replace(aws_s3_json_prefix, '').lstrip("/").replace(filename_json, '').rstrip("/")
        gc_path = json_path.replace("/json/", "/pdf/").replace('.json', '.pdf')

        # Check if file is a dup.
        # Check to see if the file as been processed before
        is_process_already = audit_file_exist(filename, path)
        if is_process_already:
            failed_data = {"filename": filename, "base_path": path, "reason": "File is duplication",
                           "modified_date_dt": int(time.time())}
            audit_list = [failed_data]
            audit_failed_record(data=audit_list)
            continue

        audit_rec = {"filename": filename, "eda_path": eda_path, "base_path": base_path, "gc_path": gc_path,
                     "json_path": json_path, "is_ocr": None, "is_pds": False, "is_syn": False, "is_fpds_ng": False,
                     "is_elasticsearch": False, "is_supplementary_file_missing": False, "modified_date_dt": 0}

        audit_list = [audit_rec]
        audit_success_record(data=audit_list)
        end = time.time()
        print("-----------  Process Status -----------")
        print(f"Dataset {input_loc}")
        print(f'Time -- It took {round(end - start, 2)} seconds!')
        print("--------------------------------------")


def s3_obj_paths(aws_s3_input_json_prefix: str) -> list:
    for obj_path in Conf.s3_utils.iter_object_paths_at_prefix(prefix=aws_s3_input_json_prefix):
        path, filename = os.path.split(obj_path)
        filename_without_ext, file_extension = os.path.splitext(filename)
        if file_extension == ".json":
            yield obj_path


if __name__ == '__main__':
    run()
