import click
import json
import os
import concurrent.futures
import traceback

from urllib3.exceptions import ProtocolError

from dataPipelines.gc_eda_pipeline.conf import Conf
from dataPipelines.gc_eda_pipeline.metadata.generate_metadata import generate_metadata_data
from dataPipelines.gc_eda_pipeline.utils.eda_utils import read_extension_conf
from dataPipelines.gc_eda_pipeline.indexer.indexer import index_data_file_v2, create_index, get_es_publisher
from dataPipelines.gc_eda_pipeline.database.database import audit_fetch_all_records_for_base_path, audit_success_record, audit_failed_record
from dataPipelines.gc_eda_pipeline.utils.text_utils import clean_text
import psycopg2.extras
import time
from psycopg2.pool import ThreadedConnectionPool
from dataPipelines.gc_eda_pipeline.utils.text_utils import extract_sow_pws


data_conf_filter = read_extension_conf()

db_pool = ThreadedConnectionPool(1, 3000, host=data_conf_filter['eda']['database']['hostname'],
                                 port=data_conf_filter['eda']['database']['port'],
                                 user=data_conf_filter['eda']['database']['user'],
                                 password=data_conf_filter['eda']['database']['password'],
                                 database=data_conf_filter['eda']['database']['db'],
                                 cursor_factory=psycopg2.extras.DictCursor)

db_pool_pbis = ThreadedConnectionPool(1, 3000, host=data_conf_filter['eda']['database_pbis']['hostname'],
                                 port=data_conf_filter['eda']['database_pbis']['port'],
                                 user=data_conf_filter['eda']['database_pbis']['user'],
                                 password=data_conf_filter['eda']['database_pbis']['password'],
                                 database=data_conf_filter['eda']['database_pbis']['db'],
                                 cursor_factory=psycopg2.extras.DictCursor)


@click.command()
@click.option(
    '--aws-s3-input-pdf-prefix',
    help="""The S3 Prefix for processing data, For multi Prefix the follow is  
            piee/unarchive_pdf/edapdf_315/,piee/unarchive_pdf/edapdf_314/,piee/unarchive_pdf/edapdf_313/
        """,
    required=False,
    type=str
)

@click.option(
    '-t',
    '--workers',
    required=False,
    default=1,
    type=int,
    help="Number of threads to run within a dataset. Locally should be set to 1-20, prod/dev should be around 250",
)
def run(aws_s3_input_pdf_prefix: str, workers: int):
    ingestion(aws_s3_input_pdf_prefix=aws_s3_input_pdf_prefix,
              workers=workers)


def ingestion(aws_s3_input_pdf_prefix: str, workers: int):
    print("Starting Gamechanger Metadata/Index Pipeline")
    os.environ["AWS_METADATA_SERVICE_TIMEOUT"] = "20"
    os.environ["AWS_METADATA_SERVICE_NUM_ATTEMPTS"] = "40"

    start_app = time.time()
    # # Load Extensions configuration files.
    data_conf_filter = read_extension_conf()

    # Create EDA index
    print(f"EDA Index {data_conf_filter['eda']['eda_index']}")
    create_index(index_name=data_conf_filter['eda']['eda_index'], alias=data_conf_filter['eda']['eda_index_alias'])

    for input_loc in aws_s3_input_pdf_prefix.split(","):
        metadata_dir_task(input_loc=input_loc, workers=workers)

    print("DONE!!!!!!")
    end_app = time.time()
    print(f'Total APP time -- It took {end_app - start_app} seconds!')


def metadata_dir_task(input_loc: str, workers: int):
    print(f"Processing Directory {input_loc}")
    start = time.time()
    print(type(Conf.ch.s3_client))  # Issue if this is not call before using s3 command in threads.

    map_filename_audit_record = audit_fetch_all_records_for_base_path(db_pool, input_loc)
    total_num_files = len(map_filename_audit_record.keys())

    number_file_processed = 0
    number_file_failed = 0
    percentage_completed = 5

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        results = [executor.submit(process_doc, filename, map_filename_audit_record[filename], data_conf_filter) for
                   filename in map_filename_audit_record]
        count = 0
        none_type = type(None)
        for fut in concurrent.futures.as_completed(results):
            if not isinstance(fut, none_type):
                try:
                    if fut.result() is not None:
                        status = fut.result().get('status')
                        if "already_processed" == status:
                            # print(f"Following file {fut.result().get('filename')} was already processed, extra info: "
                            #     f"{fut.result().get('info')}")
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
        end = time.time()

        print("-----------  Process Status -----------")
        print(f"Dataset {input_loc}")
        print(f"Number files Processed {number_file_processed}")
        print(f"Number files Failed {number_file_failed}")
        print(f'Total time -- It took {round(end - start, 2)} seconds!')
        print("--------------------------------------")


def process_doc(filename: str, audit_details: dict, data_conf_filter: dict):
    os.environ["AWS_METADATA_SERVICE_TIMEOUT"] = "20"
    os.environ["AWS_METADATA_SERVICE_NUM_ATTEMPTS"] = "40"
    audit_rec = audit_details
    ex_file_s3_path = audit_rec.get('json_path')
    ex_file_s3_pdf_path = audit_rec.get('gc_path')

    path, aws_s3_output_pdf_prefix = os.path.split(ex_file_s3_pdf_path)

    try:
        if Conf.s3_utils.prefix_exists(prefix_path=ex_file_s3_path):
            raw_docparser_data = json.loads(Conf.s3_utils.object_content(object_path=ex_file_s3_path))
            raw_docparser_data['sow_pws_text_eda_ext_t'] = clean_text(extract_sow_pws(raw_docparser_data['raw_text']))
            raw_docparser_data['sow_pws_populated_b'] = False if raw_docparser_data['sow_pws_text_eda_ext_t']=="" else True

            md_data = generate_metadata_data(data_conf_filter=data_conf_filter,
                                             file=ex_file_s3_pdf_path,
                                             audit_rec=audit_rec, db_pool=db_pool, db_pool_pbis=db_pool_pbis)

            publish_es = get_es_publisher(staging_folder="/tmp", index_name=data_conf_filter['eda']['eda_index'],
                                          alias=data_conf_filter['eda']['eda_index_alias'])

            index_data_file_v2(publish_es=publish_es, metadata_file_data=md_data,
                               parsed_pdf_file_data=raw_docparser_data, ex_file_s3_path=ex_file_s3_path,
                               audit_rec=audit_rec)

            audit_list = [audit_rec]
            audit_success_record(db_pool=db_pool, data=audit_list)

            return {'filename': filename, "status": "completed", "info": "update-metadata"}
        else:
            failed_data = {"filename": filename, "base_path": path, "reason": "Extract JSON file is missing.",
                           "modified_date_dt": int(time.time())}
            audit_list = [failed_data]
            audit_failed_record(db_pool=db_pool, data=audit_list)

            return {'filename': filename, "status": "failed", "info": "unable to file docfile " + ex_file_s3_path + " file"}
    except (ProtocolError, ConnectionError) as e:
        print(e)


if __name__ == '__main__':
    run()
