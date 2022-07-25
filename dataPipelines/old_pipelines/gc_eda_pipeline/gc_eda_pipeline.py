import time

from dataPipelines.gc_eda_pipeline.conf import Conf
# from dataPipelines.gc_elasticsearch_publisher.gc_elasticsearch_publisher import ConfiguredElasticsearchPublisher
from dataPipelines.gc_eda_pipeline.indexer.eda_indexer import EDSConfiguredElasticsearchPublisher
# from dataPipelines.gc_eda_pipeline.metadata import metadata_extraction
# from dataPipelines.gc_eda_pipeline.metadata_simple_view import metadata_extraction
# from dataPipelines.gc_eda_pipeline.metadata.metadata_json import metadata_extraction
from dataPipelines.gc_eda_pipeline.metadata.metadata_json_simple import metadata_extraction
from common.document_parser.parsers.eda_contract_search.parse import parse
from dataPipelines.gc_ocr.utils import PDFOCR, OCRJobType
from common.utils.file_utils import is_pdf, is_ocr_pdf, is_encrypted_pdf
import click
import json
import os
from typing import Union
from pathlib import Path
import concurrent.futures
import hashlib
from ocrmypdf import SubprocessOutputError
from enum import Enum
import traceback


class EDAJobType(Enum):
    """
    :param NORMAL: Process New All Documents. If document as already been processed it will skip
    :param UPDATE_METADATA: Generate the metadata and pull down the docparsed json, combines them
            and insert into Elasticsearch, if record has not been index will do the entire process
    :parm REPROCESS: Reprocess, reprocess all stages
    """
    NORMAL = 'normal'
    UPDATE_METADATA = 'update_metadata'
    UPDATE_METADATA_SKIP_NEW = 'update_metadata_skip_new'
    REPROCESS = 'reprocess'
    RE_INDEX = 're_index'


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
    print("Starting Gamechanger EDA Symphony Pipeline")
    start_app = time.time()
    # Load Extensions configuration files.
    data_conf_filter = read_extension_conf()

    aws_s3_output_pdf_prefix = data_conf_filter['eda']['aws_s3_output_pdf_prefix']
    aws_s3_json_prefix = data_conf_filter['eda']['aws_s3_json_prefix']

    for input_loc in aws_s3_input_pdf_prefix.split(","):
        print(f"Processing Directory {input_loc}")
        start = time.time()
        process_type = EDAJobType(eda_job_type)

        # Create the Audit and EDA indexes
        eda_audit_publisher = create_index(index_name=data_conf_filter['eda']['audit_index'],
                                           alias=data_conf_filter['eda']['audit_index_alias'])
        eda_publisher = create_index(index_name=data_conf_filter['eda']['eda_index'],
                                     alias=data_conf_filter['eda']['eda_index_alias'])

        # Get list of files from S3
        file_list = list_of_to_process(staging_folder, input_loc)
        number_file_processed = 0
        number_file_failed = 0

        # How many elements each list should have # work around with issue on queue being over filled
        n = loop_number
        # using list comprehension
        process_list = [file_list[i * n:(i + 1) * n] for i in range((len(file_list) + n - 1) // n)]

        for item_process in process_list:
            with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
                results = [executor.submit(process_doc, file, staging_folder, data_conf_filter, workers_ocr,
                                           aws_s3_output_pdf_prefix, aws_s3_json_prefix, process_type, skip_metadata)
                           for file in item_process]

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
                                    print(f"Following file {fut.result().get('filename')} failed")
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

        end = time.time()
        audit_id = hashlib.sha256(aws_s3_output_pdf_prefix.encode()).hexdigest()
        audit_complete(audit_id=audit_id + "_" + str(time.time()), publisher=eda_audit_publisher,
                       number_of_files=number_file_processed, number_file_failed=number_file_failed,
                       directory=input_loc, modified_date=int(time.time()), duration=int(end - start))

        print(f'Total time -- It took {end - start} seconds!')
    print("DONE!!!!!!")
    end_app = time.time()
    print(f'Total APP time -- It took {end_app - start_app} seconds!')


def process_doc(file: str, staging_folder: Union[str, Path], data_conf_filter: dict, multiprocess: int,
                aws_s3_output_pdf_prefix: str, aws_s3_json_prefix: str,
                process_type: EDAJobType, skip_metadata: bool):

    # Get connections to the Elasticsearch for the audit and eda indexes
    publish_audit = get_es_publisher(staging_folder=staging_folder, index_name=data_conf_filter['eda']['audit_index'],
                                     alias=data_conf_filter['eda']['audit_index_alias'])
    publish_es = get_es_publisher(staging_folder=staging_folder, index_name=data_conf_filter['eda']['eda_index'],
                                  alias=data_conf_filter['eda']['eda_index_alias'])

    audit_rec = {"filename_s": "", "eda_path_s": "", "gc_path_s": "", "metadata_path_s": "", "json_path_s": "",
                 "metadata_type_s": "none", "is_metadata_suc_b": False, "is_ocr_b": False, "is_docparser_b": False,
                 "is_index_b": False,  "metadata_time_f": False, "ocr_time_f": 0.0, "docparser_time_f": 0.0,
                 "index_time_f": 0.0, "modified_date_dt": 0}

    path, filename = os.path.split(file)
    filename_without_ext, file_extension = os.path.splitext(filename)

    # Determine if we want to process this record
    audit_id = hashlib.sha256(file.encode()).hexdigest()
    is_process_already = publish_audit.exists(audit_id)

    re_index_only = False
    update_metadata = False
    process_file = False
    if not is_process_already:
        process_file = True
    elif process_type == EDAJobType.NORMAL and is_process_already:
        audit_rec_old = publish_audit.get_by_id(audit_id)
        successfully_process_last_time = audit_rec_old['is_index_b']
        if successfully_process_last_time:
            return {'filename': filename, "status": "already_processed"}
        else:
            process_file = True
    elif process_type == EDAJobType.NORMAL and not is_process_already:
        process_file = True
    elif (process_type == EDAJobType.UPDATE_METADATA or process_type == EDAJobType.RE_INDEX or process_type == EDAJobType.UPDATE_METADATA_SKIP_NEW) and is_process_already:
        audit_rec_old = publish_audit.get_by_id(audit_id)

        # if last time the record fail it would never have gotten to index phase,
        # so we should just re-process the record
        is_index_b = audit_rec_old['is_index_b']
        if not is_index_b:
            process_file = True
        else:
            # Check if legacy audit data
            check_if_legacy_audit_data = audit_rec_old['is_docparser_b'] if 'is_docparser_b' in audit_rec_old else None
            if check_if_legacy_audit_data is not None:
                if 'is_pds_data_b' in audit_rec_old:
                    del audit_rec_old['is_pds_data_b']
                if 'total_time_f' in audit_rec_old:
                    del audit_rec_old['total_time_f']
                if 'json_path_s' not in audit_rec_old:
                    gc_p_s_path, gc_p_sfilename = os.path.split(audit_rec_old['gc_path_s'])
                    gc_p_s_fn_without_ext, gc_path_s_file_extension = os.path.splitext(gc_p_sfilename)
                    audit_rec_old['json_path_s'] = path.replace("/pdf/", "/json/", 1) + "/" + gc_p_s_fn_without_ext + ".json"
                    audit_rec_old['metadata_path_s'] = path + "/" + gc_p_s_fn_without_ext + ".pdf.metadata"
                del audit_rec_old['is_docparser_b']
                del audit_rec_old['docparser_time_f']

            if process_type == EDAJobType.UPDATE_METADATA or process_type == EDAJobType.UPDATE_METADATA_SKIP_NEW:
                update_metadata = True
            elif process_type == EDAJobType.RE_INDEX:
                re_index_only = True
            audit_rec = audit_rec_old
    elif process_type == EDAJobType.REPROCESS:
        process_file = True
    else:
        process_file = False

    # Download the docparser json file and metadata file
    if re_index_only:
        # Metadata
        md_file_s3_path = aws_s3_output_pdf_prefix + "/" + file + ".metadata"
        md_file_local_path = staging_folder + "/pdf/" + file + ".metadata"
        Conf.s3_utils.download_file(file=md_file_local_path, object_path=md_file_s3_path)

        # Docparsered json
        ex_file_local_path = staging_folder + "/json/" + path + "/" + filename_without_ext + ".json"
        ex_file_s3_path = aws_s3_json_prefix + "/" + path + "/" + filename_without_ext + ".json"
        Conf.s3_utils.download_file(file=ex_file_local_path, object_path=ex_file_s3_path)

        # Index into Elasticsearch
        index_output_file_path = index(staging_folder=staging_folder, publish_es=publish_es, path=path,
                                       filename_without_ext=filename_without_ext, md_file_local_path=md_file_local_path,
                                       ex_file_local_path=ex_file_local_path, ex_file_s3_path=ex_file_s3_path,
                                       audit_id=audit_id, audit_rec=audit_rec, publish_audit=publish_audit)

        # Delete for local file system to free up space.
        files_delete = [md_file_local_path, ex_file_local_path, index_output_file_path]
        cleanup_record(files_delete)

        return {'filename': filename, "status": "completed", "info": "re-indexed"}

    elif update_metadata:
        # Generate metadata file
        md_file_s3_path, md_file_local_path = generate_metadata_file(staging_folder=staging_folder,
                                                                     data_conf_filter=data_conf_filter, file=file,
                                                                     filename=filename,
                                                                     aws_s3_output_pdf_prefix=aws_s3_output_pdf_prefix,
                                                                     audit_id=audit_id, audit_rec=audit_rec,
                                                                     publish_audit=publish_audit, skip_metadata=skip_metadata)

        # Docparsered json
        ex_file_local_path = staging_folder + "/json/" + path + "/" + filename_without_ext + ".json"
        ex_file_s3_path = aws_s3_json_prefix + "/" + path + "/" + filename_without_ext + ".json"
        Conf.s3_utils.download_file(file=ex_file_local_path, object_path=ex_file_s3_path)

        # Index into Elasticsearch
        index_output_file_path = index(staging_folder=staging_folder, publish_es=publish_es, path=path,
                                       filename_without_ext=filename_without_ext, md_file_local_path=md_file_local_path,
                                       ex_file_local_path=ex_file_local_path, ex_file_s3_path=ex_file_s3_path,
                                       audit_id=audit_id, audit_rec=audit_rec, publish_audit=publish_audit)

        # Delete for local file system to free up space.
        files_delete = [md_file_local_path, ex_file_local_path, index_output_file_path]
        cleanup_record(files_delete)

        return {'filename': filename, "status": "completed", "info": "update-metadata"}

    elif process_file and process_type == EDAJobType.UPDATE_METADATA_SKIP_NEW:
        if is_process_already:
            return {'filename': filename, "status": "already_processed", "info": "File might be incorrect type or corrupted"}
        else:
            return {'filename': filename, "status": "skip", "info": "File was skip"}

    elif process_file:
        files_delete = []
        # Generate metadata file
        md_file_s3_path, md_file_local_path = generate_metadata_file(staging_folder=staging_folder,
                                                                     data_conf_filter=data_conf_filter, file=file,
                                                                     filename=filename,
                                                                     aws_s3_output_pdf_prefix=aws_s3_output_pdf_prefix,
                                                                     audit_id=audit_id, audit_rec=audit_rec,
                                                                     publish_audit=publish_audit, skip_metadata=skip_metadata)
        files_delete.append(md_file_local_path)

        # Download PDF file/OCR PDF if need
        is_pdf_file, pdf_file_local_path, pdf_file_s3_path = ocr_process(staging_folder=staging_folder, file=file,
                                                                         multiprocess=multiprocess,
                                                                         aws_s3_output_pdf_prefix=aws_s3_output_pdf_prefix,
                                                                         audit_id=audit_id, audit_rec=audit_rec,
                                                                         publish_audit=publish_audit)
        files_delete.append(pdf_file_local_path)
        # Doc Parser/ Extract Text
        if is_pdf_file and os.path.exists(pdf_file_local_path):
            ex_file_local_path, ex_file_s3_path, is_extract_suc = extract_text(staging_folder=staging_folder,
                                                                               path=path,
                                                                               pdf_file_local_path=pdf_file_local_path,
                                                                               filename_without_ext=filename_without_ext,
                                                                               aws_s3_json_prefix=aws_s3_json_prefix,
                                                                               audit_id=audit_id, audit_rec=audit_rec,
                                                                               publish_audit=publish_audit)
            files_delete.append(pdf_file_local_path)
            if is_extract_suc:
                # Index into Elasticsearch
                index_output_file_path = index(staging_folder=staging_folder, publish_es=publish_es, path=path,
                                               filename_without_ext=filename_without_ext,
                                               md_file_local_path=md_file_local_path, ex_file_local_path=ex_file_local_path,
                                               ex_file_s3_path=ex_file_s3_path, audit_id=audit_id, audit_rec=audit_rec,
                                               publish_audit=publish_audit)
                files_delete.append(index_output_file_path)
                # Delete for local file system to free up space.
                cleanup_record(files_delete)
                return {'filename': filename, "status": "completed", "info": "new record"}
            else:
                # Delete for local file system to free up space.
                cleanup_record(files_delete)
                return {'filename': filename, "status": "failed", "info": "Not a PDF file"}

    return {'filename': filename, "status": "failed", "info": "failed -- Didn't match any processing type"}


def generate_metadata_file(staging_folder: str, data_conf_filter: dict, file: str, filename: str,
                           aws_s3_output_pdf_prefix: str, audit_id: str, audit_rec: dict,
                           publish_audit: EDSConfiguredElasticsearchPublisher, skip_metadata: bool):

    md_file_local_path = staging_folder + "/pdf/" + file + ".metadata"
    md_file_s3_path = aws_s3_output_pdf_prefix + "/" + file + ".metadata"

    pds_start = time.time()

    is_md_successful, is_supplementary_file_missing, md_type, data = metadata_extraction(staging_folder, file, data_conf_filter, aws_s3_output_pdf_prefix, skip_metadata)

    with open(md_file_local_path, "w") as output_file:
        json.dump(data, output_file)

    Conf.s3_utils.upload_file(file=md_file_local_path, object_name=md_file_s3_path)
    pds_end = time.time()
    time_md = pds_end - pds_start

    audit_rec.update({"filename_s": filename, "eda_path_s": file, "metadata_path_s": md_file_s3_path,
                      "metadata_type_s": md_type, "is_metadata_suc_b": is_md_successful,
                      "is_supplementary_file_missing": is_supplementary_file_missing,
                      "metadata_time_f": round(time_md, 4), "modified_date_dt": int(time.time())})
    audit_record_new(audit_id=audit_id, publisher=publish_audit, audit_record=audit_rec)

    return md_file_s3_path, md_file_local_path


def ocr_process(staging_folder: str, file: str, multiprocess: int, aws_s3_output_pdf_prefix: str, audit_id: str,
                audit_rec: dict, publish_audit: EDSConfiguredElasticsearchPublisher):

    # Download PDF file
    ocr_time_start = time.time()
    pdf_file_local_path = staging_folder + "/pdf/" + file
    saved_file = Conf.s3_utils.download_file(file=pdf_file_local_path, object_path=file)

    # OCR PDF if need
    is_pdf_file, is_ocr = pdf_ocr(file=file, staging_folder=staging_folder, multiprocess=multiprocess)

    # Copy PDF into S3
    pdf_file_s3_path = aws_s3_output_pdf_prefix + "/" + file
    Conf.s3_utils.upload_file(file=saved_file, object_name=pdf_file_s3_path)
    ocr_time_end = time.time()
    time_ocr = ocr_time_end - ocr_time_start

    audit_rec.update({"gc_path_s": pdf_file_s3_path, "is_ocr_b": is_ocr, "ocr_time_f": round(time_ocr, 4),
                      "modified_date_dt": int(time.time())})
    audit_record_new(audit_id=audit_id, publisher=publish_audit, audit_record=audit_rec)

    return is_pdf_file, pdf_file_local_path, pdf_file_s3_path


def extract_text(staging_folder: str, pdf_file_local_path: str, path: str, filename_without_ext: str,
                 aws_s3_json_prefix: str, audit_id: str, audit_rec: dict,
                 publish_audit: EDSConfiguredElasticsearchPublisher):
    is_extract_suc = False
    doc_time_start = time.time()
    ex_file_local_path = staging_folder + "/json/" + path + "/" + filename_without_ext + ".json"
    ex_file_s3_path = aws_s3_json_prefix + "/" + path + "/" + filename_without_ext + ".json"

    docparser(metadata_file_path=None, saved_file=pdf_file_local_path, staging_folder=staging_folder, path=path)
    if os.path.exists(ex_file_local_path):
        Conf.s3_utils.upload_file(file=ex_file_local_path,  object_name=ex_file_s3_path)
        is_extract_suc = True
    else:
        is_extract_suc = False

    doc_time_end = time.time()
    time_dp = doc_time_end - doc_time_start

    audit_rec.update({"json_path_s": ex_file_s3_path, "is_docparser_b": is_extract_suc,
                      "docparser_time_f": round(time_dp, 4), "modified_date_dt": int(time.time())})
    audit_record_new(audit_id=audit_id, publisher=publish_audit, audit_record=audit_rec)

    return ex_file_local_path, ex_file_s3_path, is_extract_suc


def index(publish_es: EDSConfiguredElasticsearchPublisher, staging_folder: str, md_file_local_path: str,
          ex_file_local_path: str, path: str, filename_without_ext: str, ex_file_s3_path: str, audit_id: str,
          audit_rec: dict, publish_audit: EDSConfiguredElasticsearchPublisher):

    index_start = time.time()

    with open(md_file_local_path) as metadata_file:
        metadata_file_data = json.load(metadata_file)

    with open(ex_file_local_path) as parsed_pdf_file:
        parsed_pdf_file_data = json.load(parsed_pdf_file)

    if 'extensions' in metadata_file_data.keys():
        extensions_json = metadata_file_data["extensions"]
        parsed_pdf_file_data = {**parsed_pdf_file_data, **extensions_json}
        del metadata_file_data['extensions']

    index_json_data = {**parsed_pdf_file_data, **metadata_file_data}

    index_output_file_path = staging_folder + "/index/" + path + "/" + filename_without_ext + ".index.json"
    with open(index_output_file_path, "w") as output_file:
        json.dump(index_json_data, output_file)

    is_index = publish_es.index_json(index_output_file_path, ex_file_s3_path)
    index_end = time.time()
    time_index = index_end - index_start

    audit_rec.update({"is_index_b": is_index, "index_time_f": round(time_index, 4),
                      "modified_date_dt": int(time.time())})
    audit_record_new(audit_id=audit_id, publisher=publish_audit, audit_record=audit_rec)
    return index_output_file_path


def create_index(index_name: str, alias: str):
    publisher = EDSConfiguredElasticsearchPublisher(index_name=index_name, ingest_dir="",  alias=alias)
    publisher.create_index()
    if alias:
        publisher.update_alias()
    return publisher


def get_es_publisher(staging_folder: str, index_name: str, alias: str) -> EDSConfiguredElasticsearchPublisher:
    publisher = EDSConfiguredElasticsearchPublisher(index_name=index_name, ingest_dir=staging_folder,
                                                 alias=alias)
    return publisher


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


def read_extension_conf() -> dict:
    ext_app_config_name = os.environ.get("GC_APP_CONFIG_EXT_NAME")
    with open(ext_app_config_name) as json_file:
        data = json.load(json_file)
    return data


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


def pdf_ocr(file: str, staging_folder: str, multiprocess: int) -> (bool, bool):
    try:
        path, filename = os.path.split(file)
        is_ocr = False
        is_pdf_file = False
        if filename != "" and Conf.s3_utils.object_exists(object_path=file):
            saved_file = Conf.s3_utils.download_file(file=staging_folder + "/pdf/" + file, object_path=file)
            if not is_pdf(str(saved_file)):
                return is_pdf_file, is_ocr
            else:
                is_pdf_file = True
            try:
                if is_pdf(str(saved_file)) and not is_ocr_pdf(str(saved_file)) and not is_encrypted_pdf(str(saved_file)):
                    is_pdf_file = True
                    ocr = PDFOCR(
                        input_file=saved_file,
                        output_file=saved_file,
                        ocr_job_type=OCRJobType.SKIP_TEXT,
                        ignore_init_errors=True,
                        num_threads=multiprocess
                    )
                    try:
                        is_ocr = ocr.convert()
                    except SubprocessOutputError as e:
                        print(e)
                        is_ocr = False
            except Exception as ex:
                print(ex)
                is_ocr = False
            return is_pdf_file, is_ocr
    except RuntimeError as e:
        print(f"File does not look like a pdf file {saved_file}")
        traceback.print_exc()
        is_pdf_file = False
        is_ocr = False
        return is_pdf_file, is_ocr

    return is_pdf_file, is_ocr


def docparser(metadata_file_path: str, saved_file: Union[str, Path], staging_folder: Union[str, Path], path: str) \
        -> bool:
    """
    OCR will be done outside of the docparser.
    """
    m_file = saved_file
    out_dir = staging_folder + "/json/" + path + "/"
    parse(f_name=m_file, meta_data=metadata_file_path, ocr_missing_doc=False, num_ocr_threads=1, out_dir=out_dir)
    return True


def audit_record_new(audit_id: str, publisher: EDSConfiguredElasticsearchPublisher, audit_record: dict):
    publisher.insert_record(id_record=audit_id, json_record=audit_record)


def cleanup_record(delete_files: list):
    pass
    for delete_file in delete_files:
        if os.path.exists(delete_file):
            os.remove(delete_file)


def audit_complete(audit_id: str, publisher: EDSConfiguredElasticsearchPublisher, directory: str, number_of_files: int,
                   number_file_failed: int, modified_date: int, duration: int):
    ar = {
        "completed": "completed",
        "directory_s": directory,
        "number_of_files_l": number_of_files,
        "number_file_failed_l": number_file_failed,
        "modified_date_dt": modified_date,
        "duration_l": duration
    }
    publisher.insert_record(id_record=audit_id, json_record=ar)


if __name__ == '__main__':
    run()
