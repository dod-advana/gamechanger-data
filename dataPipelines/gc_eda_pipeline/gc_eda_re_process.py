import os
import time
import click
import concurrent.futures
import traceback
import hashlib
import shutil

from dataPipelines.gc_eda_pipeline.conf import Conf
from dataPipelines.gc_eda_pipeline.utils.eda_utils import read_extension_conf
from dataPipelines.gc_eda_pipeline.audit.audit import audit_complete
from dataPipelines.gc_eda_pipeline.metadata.generate_metadata_file import generate_metadata_file
from dataPipelines.gc_eda_pipeline.indexer.indexer import combine_metadata_docparser, create_index, get_es_publisher
from dataPipelines.gc_eda_pipeline.utils.eda_job_type import EDAJobType

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
    start_app = time.time()
    print("Starting Gamechanger EDA Symphony Pipeline - Reprocessing")

    os.environ["AWS_METADATA_SERVICE_TIMEOUT"] = "10"
    os.environ["AWS_METADATA_SERVICE_NUM_ATTEMPTS"] = "10"

    for input_loc in aws_s3_input_pdf_prefix.split(","):
        print(f"Processing Directory {input_loc}")

        process_type = EDAJobType.UPDATE_METADATA_SKIP_NEW

        start = time.time()
        # Load Extensions configuration files.
        data_conf_filter = read_extension_conf()

        aws_s3_output_pdf_prefix = data_conf_filter['eda']['aws_s3_output_pdf_prefix']
        aws_s3_json_prefix = data_conf_filter['eda']['aws_s3_json_prefix']

        # Create the Audit and EDA indexes
        eda_audit_publisher = create_index(index_name=data_conf_filter['eda']['audit_index'],
                                           alias=data_conf_filter['eda']['audit_index_alias'])

        create_local_folders(staging_folder=staging_folder, input_loc=input_loc)

        # Download docparsed files
        docparser_dir = aws_s3_json_prefix + "/" + input_loc
        # print(f"input_loc: {input_loc}")
        local_staging_dir = staging_folder + "/json/" + input_loc
        # print(f"docparser_dir {docparser_dir}")
        Conf.s3_utils.download_dir(local_dir=local_staging_dir, prefix_path=docparser_dir, max_threads=max_workers)

        p = Path(local_staging_dir).glob("**/*.json")
        file_list = [str(x) for x in p if x.is_file()]

        number_file_processed = 0
        number_file_failed = 0

        # How many elements each list should have # work around with issue on queue being over filled
        n = loop_number
        # using list comprehension
        process_list = [file_list[i * n:(i + 1) * n] for i in range((len(file_list) + n - 1) // n)]

        for item_process in process_list:
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                results = [executor.submit(process_doc, file, staging_folder, data_conf_filter, workers_ocr, aws_s3_output_pdf_prefix, aws_s3_json_prefix, process_type, skip_metadata) for file in item_process]

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
                                    print(f"Following file {fut.result().get('filename')} failed , extra info: "
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
                        

        start_bulk_index = time.time()
        eda_publisher = create_index(index_name=data_conf_filter['eda']['eda_index'],
                                     alias=data_conf_filter['eda']['eda_index_alias'], ingest_dir=staging_folder + "/index/" + input_loc + "/")
        eda_publisher.index_jsons()
        end_bulk_index = time.time()


        delete_dir = []
        delete_dir.append(staging_folder + "/pdf/" + input_loc)
        delete_dir.append(staging_folder + "/json/" + input_loc)
        delete_dir.append(staging_folder + "/index/" + input_loc)
        delete_dir.append(staging_folder + "/supplementary_data/")
        # cleanup_record(delete_dir)

        end = time.time()
        audit_id = hashlib.sha256(aws_s3_output_pdf_prefix.encode()).hexdigest()
        audit_complete(audit_id=audit_id + "_" + str(time.time()), publisher=eda_audit_publisher,
                       number_of_files=number_file_processed, number_file_failed=number_file_failed,
                       directory=input_loc, modified_date=int(time.time()), duration=int(end - start), bulk_index=float(end_bulk_index - start_bulk_index))
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

    path, filename = os.path.split(file)
    filename_without_ext, file_extension = os.path.splitext(filename)

    # Determine if we want to process this record
    pdf_name = path.replace(staging_folder + "/json/", "") + "/" + filename_without_ext + ".pdf"
    index_name = path.replace(staging_folder + "/json/", "") + "/" + filename_without_ext + ".json"
    # print("------------------------------------")
    # print(f"staging_folder: {staging_folder}")
    # print(f"pdf_name: {pdf_name}")
    # print(f"index_name: {index_name}")

    audit_id = hashlib.sha256(pdf_name.encode()).hexdigest()
    is_process_already = publish_audit.exists(audit_id)
    # print(f"audit_id: {audit_id}")
    # print(f"is_process_already: {is_process_already}")
    # print("------------------------------------")

    if is_process_already:
        audit_rec = publish_audit.get_by_id(audit_id)
        json_path_s = audit_rec.get("json_path_s")
        if not json_path_s:
            return {'filename': filename, "status": "failed", "info": "unable to find `id` in audit"}
    else:
        return {'filename': filename, "status": "failed", "info": "file was not process before"}

    record_id_encode = hashlib.sha256(json_path_s.encode()).hexdigest()
    md_file_s3_path, md_file_local_path = generate_metadata_file(staging_folder=staging_folder,
                                                                 data_conf_filter=data_conf_filter, file=pdf_name,
                                                                 filename=filename,
                                                                 aws_s3_output_pdf_prefix=aws_s3_output_pdf_prefix,
                                                                 audit_id=audit_id, audit_rec=audit_rec,
                                                                 publish_audit=publish_audit,
                                                                 skip_metadata=skip_metadata)

    index_json_loc = combine_metadata_docparser(staging_folder=staging_folder, md_file_local_path=md_file_local_path,
                                                doc_file_local_path=file, index_file_local_path=index_name, record_id=record_id_encode)

    return {'filename': filename, "status": "completed", "info": "create_index_json_file"}


def create_local_folders(staging_folder: Union[str, Path], input_loc: str):
    if not os.path.exists(staging_folder + "/pdf/" + input_loc + "/"):
        os.makedirs(staging_folder + "/pdf/" + input_loc + "/")
    if not os.path.exists(staging_folder + "/json/" + input_loc + "/"):
        os.makedirs(staging_folder + "/json/" + input_loc + "/")
    if not os.path.exists(staging_folder + "/index/" + input_loc + "/"):
        os.makedirs(staging_folder + "/index/" + input_loc + "/")
    if not os.path.exists(staging_folder + "/supplementary_data/"):
        os.makedirs(staging_folder + "/supplementary_data/")


def cleanup_record(delete_files: list):
    for delete_file in delete_files:
        try:
            shutil.rmtree(delete_file)
        except OSError as e:
            print("Error: %s : %s" % (delete_file, e.strerror))


if __name__ == '__main__':
    run()