import os
import time
import click
import concurrent.futures
import traceback
import hashlib
import shutil
import json

from dataPipelines.gc_eda_pipeline.conf import Conf
from dataPipelines.gc_eda_pipeline.utils.eda_utils import read_extension_conf
from dataPipelines.gc_eda_pipeline.audit.audit import audit_complete
from dataPipelines.gc_eda_pipeline.metadata.generate_metadata_file import generate_metadata_data
from dataPipelines.gc_eda_pipeline.indexer.indexer import combine_metadata_docparser_data, create_index, get_es_publisher
from dataPipelines.gc_eda_pipeline.utils.eda_job_type import EDAJobType

from urllib3.exceptions import ProtocolError

from pathlib import Path
from typing import Union


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
@click.option(
    '--skip-metadata',
    help="""Skip the step to Generate the metadata file and create generic metadata file, that includes will ony work 
                with EDAJobType(NORMAL, REPROCESS, UPDATE_METADATA, UPDATE_METADATA_SKIP_NEW) not RE_INDEX """,
    required=False,
    type=bool,
    default=False,
)
def run(staging_folder: str, aws_s3_input_pdf_prefix: str,
        max_workers: int, workers_ocr: int, eda_job_type: str, loop_number: int, skip_metadata: bool):
    print("Starting Gamechanger EDA Symphony Pipeline - Reprocessing ---- 4.25.2021")
    os.environ["AWS_METADATA_SERVICE_TIMEOUT"] = "10"
    os.environ["AWS_METADATA_SERVICE_NUM_ATTEMPTS"] = "40"

    start_app = time.time()

    # Load Extensions configuration files.
    data_conf_filter = read_extension_conf()
    aws_s3_output_pdf_prefix = data_conf_filter['eda']['aws_s3_output_pdf_prefix']
    aws_s3_json_prefix = data_conf_filter['eda']['aws_s3_json_prefix']

    process_type = EDAJobType.UPDATE_METADATA_SKIP_NEW

    # Create the Audit and EDA indexes
    eda_audit_publisher = create_index(index_name=data_conf_filter['eda']['audit_index'],
                                       alias=data_conf_filter['eda']['audit_index_alias'])


    # eda_publisher.update_settings()


    for input_loc in aws_s3_input_pdf_prefix.split(","):
        print(f"Processing Directory {input_loc}")
        start = time.time()

        # create_local_folders(staging_folder=staging_folder, input_loc=input_loc)

        # # Download docparsed files


        # p = Path(local_staging_dir).glob("**/*.json")
        # file_list = [str(x) for x in p if x.is_file()]

        # Get list of files from S3
        file_list = list_of_to_process(staging_folder, input_loc)
        total_num_files = len(file_list)
        number_file_processed = 0
        number_file_failed = 0



        # How many elements each list should have # work around with issue on queue being over filled
        # n = loop_number
        # using list comprehension
        # process_list = [file_list[i * n:(i + 1) * n] for i in range((len(file_list) + n - 1) // n)]
        #
        # files_group = list(split(file_list, max_workers)
        # print(files_group)

        # for item_process in process_list:
        with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
            results = [executor.submit(process_doc, file, staging_folder, data_conf_filter, workers_ocr, aws_s3_output_pdf_prefix, aws_s3_json_prefix, process_type, skip_metadata) for file in file_list]

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
                    except Exception as exc:
                        value = str(exc)
                        if value == "not a PDF":
                            print("EDA ****  File is not a PDF **** EDA")
                        else:
                            print(f"EDA **** Failed to process '{exc}'  ****  EDA")
                            traceback.print_exc()
                        number_file_failed = number_file_failed + 1
                    except RuntimeError as re:
                        print(f"EDA **** Failed to process '{re}'  ****  EDA")
                        traceback.print_exc()
                else:
                    print("EDA ****  File is not a PDF **** EDA")

        print(f"Number files Processed {number_file_processed}")
        print(f"Number files Failed {number_file_failed}")

        start_bulk_index = time.time()
        eda_publisher = create_index(index_name=data_conf_filter['eda']['eda_index'],
                                     alias=data_conf_filter['eda']['eda_index_alias'], ingest_dir=staging_folder + "/index/" + input_loc + "/")
        eda_publisher.index_jsons()
        end_bulk_index = time.time()



        delete_dir = []
        delete_dir.append(staging_folder + "/pdf/" + input_loc)
        delete_dir.append(staging_folder + "/json/" + input_loc)
        delete_dir.append(staging_folder + "/index/" + input_loc)
        delete_dir.append(staging_folder + "/supplementary_datas/")
        cleanup_record(delete_dir)

        end = time.time()
        audit_id = hashlib.sha256(aws_s3_output_pdf_prefix.encode()).hexdigest()
        audit_complete(audit_id=audit_id + "_" + str(time.time()), publisher=eda_audit_publisher,
                       number_of_files=number_file_processed, number_file_failed=number_file_failed,
                       directory=input_loc, modified_date=int(time.time()), duration=int(end - start), bulk_index=float(end_bulk_index - start_bulk_index))
        print(f"Time to index into Elasticsearch: {float(end_bulk_index - start_bulk_index)}")

        print(f'Total time -- It took {end - start} seconds!')
    print("DONE!!!!!!")
    end_app = time.time()

    print(f'Total APP time -- It took {end_app - start_app} seconds!')


def process_doc(file: str, staging_folder: Union[str, Path], data_conf_filter: dict, multiprocess: int,
                aws_s3_output_pdf_prefix: str, aws_s3_json_prefix: str,
                process_type: EDAJobType, skip_metadata: bool):
    os.environ["AWS_METADATA_SERVICE_TIMEOUT"] = "20"
    os.environ["AWS_METADATA_SERVICE_NUM_ATTEMPTS"] = "40"

    # Get connections to the Elasticsearch for the audit and eda indexes
    publish_audit = get_es_publisher(staging_folder=staging_folder, index_name=data_conf_filter['eda']['audit_index'],
                                     alias=data_conf_filter['eda']['audit_index_alias'])

    publish_es = get_es_publisher(staging_folder=staging_folder, index_name=data_conf_filter['eda']['eda_index'],
                                  alias=data_conf_filter['eda']['eda_index_alias'])

    path, filename = os.path.split(file)
    filename_without_ext, file_extension = os.path.splitext(filename)
    # Determine if we want to process this record
    pdf_name = path.replace(staging_folder + "/json/", "") + "/" + filename_without_ext + ".pdf"
    index_name = path.replace(staging_folder + "/json/", "") + "/" + filename_without_ext + ".json"

    audit_id = hashlib.sha256(pdf_name.encode()).hexdigest()
    is_process_already = publish_audit.exists(audit_id)

    error_count = 0
    index_json_created = False
    fail = False

    if is_process_already:
        audit_rec = publish_audit.get_by_id(audit_id)
        json_path_s = audit_rec.get("json_path_s")
        if not json_path_s:
            return {'filename': filename, "status": "failed", "info": "unable to find `id` in audit"}
    else:
        return {'filename': filename, "status": "failed", "info": "file was not process before"}

    while not index_json_created and not fail:
        try:
            # Docparsered json
            ex_file_local_path = staging_folder + "/json/" + path + "/" + filename_without_ext + ".json"
            ex_file_s3_path = aws_s3_json_prefix + "/" + path + "/" + filename_without_ext + ".json"
            if Conf.s3_utils.object_exists(object_path=ex_file_s3_path):
                Conf.s3_utils.download_file(file=ex_file_local_path, object_path=ex_file_s3_path)
                # raw_supplementary_data = json.loads(Conf.s3_utils.object_content(object_path=ex_file_s3_path))

                record_id_encode = hashlib.sha256(json_path_s.encode()).hexdigest()
                # record_id_encode = json_path_s;
                md_file_s3_path, md_file_local_path, md_data = generate_metadata_data(staging_folder=staging_folder,
                                                                             data_conf_filter=data_conf_filter, file=pdf_name,
                                                                             filename=filename,
                                                                             aws_s3_output_pdf_prefix=aws_s3_output_pdf_prefix,
                                                                             audit_id=audit_id, audit_rec=audit_rec,
                                                                             publish_audit=publish_audit,
                                                                             skip_metadata=skip_metadata)

                combine_metadata_docparser_data(publish_es=publish_es, staging_folder=staging_folder, md_file_local_path=md_file_local_path,
                                                            doc_file_local_path=ex_file_local_path, index_file_local_path=index_name, record_id=record_id_encode, md_data=md_data)
            else:
                return {'filename': filename, "status": "failed", "info": "unable to file docfile " +ex_file_s3_path + " file"}
            
        except (ProtocolError, ConnectionError) as e:
            error_count += 1
            time.sleep(1)
        else:
            index_json_created = True
        finally:
            if error_count > 10:
                print(f"Tried to get generate index json for file {filename}")
                return {'filename': filename, "status": "failed", "info": "unable to create index file"}

    return {'filename': filename, "status": "completed", "info": "create_index_json_file"}


# def create_local_folders(staging_folder: Union[str, Path], input_loc: str):
#     if not os.path.exists(staging_folder + "/pdf/" + input_loc + "/"):
#         os.makedirs(staging_folder + "/pdf/" + input_loc + "/")
#     if not os.path.exists(staging_folder + "/json/" + input_loc + "/"):
#         os.makedirs(staging_folder + "/json/" + input_loc + "/")
#     if not os.path.exists(staging_folder + "/index/" + input_loc + "/"):
#         os.makedirs(staging_folder + "/index/" + input_loc + "/")
#     if not os.path.exists(staging_folder + "/supplementary_data/"):
#         os.makedirs(staging_folder + "/supplementary_data/")


def cleanup_record(delete_files: list):
    for delete_file in delete_files:
        try:
            shutil.rmtree(delete_file)
        except OSError as e:
            print("Error: %s : %s" % (delete_file, e.strerror))



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
            if not os.path.exists(staging_folder + "/supplementary_data/"):
                os.makedirs(staging_folder + "/supplementary_data/")
    return files


def split(a, n):
    k, m = divmod(len(a), n)
    return (a[i*k+min(i, m):(i+1)*k+min(i+1, m)] for i in range(n))

if __name__ == '__main__':
    run()