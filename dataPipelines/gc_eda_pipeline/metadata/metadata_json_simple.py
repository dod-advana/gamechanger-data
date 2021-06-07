import psycopg2
from psycopg2.extras import RealDictCursor
import os
import time
import json
from datetime import datetime
from dataPipelines.gc_eda_pipeline.conf import Conf
from typing import Union
from pathlib import Path
import traceback
from dataPipelines.gc_eda_pipeline.metadata.pds_extract_json import extract_pds
from dataPipelines.gc_eda_pipeline.metadata.syn_extract_json import extract_syn
from dataPipelines.gc_eda_pipeline.metadata.metadata_util import title

from urllib3.exceptions import ProtocolError


def metadata_extraction(staging_folder: Union[str, Path], filename_input: str, data_conf_filter: dict,
                        aws_s3_output_pdf_prefix: str, skip_metadata: bool):

    postfix_es = data_conf_filter['eda']['postfix_es']

    path, filename = os.path.split(filename_input)
    filename_without_ext, file_extension = os.path.splitext(filename)
    data = {"access_timestamp": str(datetime.now()), 'doc_name': filename_without_ext,
            'doc_title': title(filename_without_ext), 'title': title(filename_without_ext)}
    extensions_metadata = {}

    is_supplementary_file_missing = False
    if skip_metadata:
        metadata_type = "skipped"
        extensions_metadata["metadata_type" + postfix_es] = metadata_type
        extensions_metadata['dir_location_eda_ext'] = path
        extensions_metadata['file_location_eda_ext'] = aws_s3_output_pdf_prefix + "/" + filename_input
        data['doc_title'] = title(filename_without_ext)
        is_md_successful = False
        return is_md_successful, is_supplementary_file_missing, metadata_type, data

    sql_check_if_syn_metadata_exist = data_conf_filter['eda']['sql_check_if_syn_metadata_exist']
    sql_check_if_pds_metadata_exist = data_conf_filter['eda']['sql_check_if_pds_metadata_exist']

    global date_fields_l
    date_fields_l = data_conf_filter['eda']['sql_filter_fields']['date']
    operating_environment = data_conf_filter['eda']['operating_environment']

    metadata_type = "none"
    conn = None
    cursor = None

    try:
        conn = psycopg2.connect(host=data_conf_filter['eda']['database']['hostname'],
                                port=data_conf_filter['eda']['database']['port'],
                                user=data_conf_filter['eda']['database']['user'],
                                password=data_conf_filter['eda']['database']['password'],
                                dbname=data_conf_filter['eda']['database']['db'],
                                cursor_factory=psycopg2.extras.DictCursor)
        cursor = conn.cursor()

        is_pds_data = False
        is_syn_data = False
        metadata_type = "none"
        s3_supplementary_data = ""
        metadata_filename = ""
        local_supplementary_data = ""
        s3_location = ""

        # Check if file has metadata from PDS
        cursor.execute(sql_check_if_pds_metadata_exist, (filename,))
        is_pds_metadata = cursor.fetchone()

        if is_pds_metadata is not None:
            # Get General PDS Metadata
            for col_name in [desc[0] for desc in cursor.description]:
                if is_pds_metadata[col_name] is not None:
                    val = is_pds_metadata[col_name]
                    if col_name in date_fields_l and val is not None and val is not '':
                        extensions_metadata[col_name + postfix_es + "_dt"] = val
                    else:
                        extensions_metadata[col_name + postfix_es] = val

            if is_pds_metadata['pds_json_filename'] is not None and is_pds_metadata['pds_json_filename'] is not '':
                is_pds_data = True
                is_syn_data = False
                metadata_type = "pds"
                metadata_filename = is_pds_metadata['pds_json_filename']
                s3_location = is_pds_metadata['s3_loc']

        if not is_pds_data:
            # Check if file has metadata from SYN
            cursor.execute(sql_check_if_syn_metadata_exist, (filename,))
            is_syn_metadata = cursor.fetchone()
            if is_syn_metadata is not None:
                # Get General SYN Metadata
                for col_name in [desc[0] for desc in cursor.description]:
                    if is_syn_metadata[col_name] is not None:
                        val = is_syn_metadata[col_name]
                        if col_name in date_fields_l and val is not None and val is not '':
                            extensions_metadata[col_name + postfix_es + "_dt"] = val
                        else:
                            extensions_metadata[col_name + postfix_es] = val

                if is_syn_metadata['syn_json_filename'] is not None and is_syn_metadata['syn_json_filename'] is not '':
                    is_pds_data = False
                    is_syn_data = True
                    metadata_type = "syn"
                    metadata_filename = is_syn_metadata['syn_json_filename']
                    s3_location = is_syn_metadata['s3_loc']
            else:
                is_pds_data = False
                is_syn_data = False
                metadata_type = "none"

        extensions_metadata["metadata_type" + postfix_es] = metadata_type
        extensions_metadata['dir_location_eda_ext'] = path
        extensions_metadata['file_location_eda_ext'] = aws_s3_output_pdf_prefix + "/" + filename_input
        data['doc_title'] = title(filename_without_ext)

        if is_pds_data:
            # Download File from S3
            local_supplementary_data = staging_folder + "/supplementary_data/" + metadata_filename
            s3_location = s3_location.strip()
            if operating_environment == "dev":
                s3_supplementary_data = s3_location.replace("s3://advana-raw-zone/", "")
            else:
                s3_supplementary_data = s3_location.replace("s3://advana-eda-wawf-restricted/", "")

        if is_syn_data:
            # Download File from S3
            local_supplementary_data = staging_folder + "/supplementary_data/" + metadata_filename
            s3_location = s3_location.strip()
            if operating_environment == "dev":
                s3_supplementary_data = s3_location.replace("s3://advana-raw-zone/", "")
            else:
                s3_supplementary_data = s3_location.replace("s3://advana-eda-wawf-restricted/", "")

        if (is_pds_data or is_syn_data) and metadata_filename is not None and metadata_filename != "":
            if Conf.s3_utils.prefix_exists(prefix_path=s3_supplementary_data):
                get_metadata_file = False
                error_count = 0
                while not get_metadata_file and error_count < 10:
                    try:
                        raw_supplementary_data = json.loads(Conf.s3_utils.object_content(object_path=s3_supplementary_data))
                    except (ProtocolError, ConnectionError) as e:
                        error_count += 1
                        time.sleep(1)
                    else:
                        get_metadata_file = True


                # Conf.s3_utils.download_file(file=local_supplementary_data, object_path=s3_supplementary_data)

                # with open(local_supplementary_data) as json_file:
                #     raw_supplementary_data = json.load(json_file)

                if is_pds_data and get_metadata_file:
                    extracted_data = extract_pds(data_conf_filter=data_conf_filter, data=raw_supplementary_data, extensions_metadata=extensions_metadata)

                if is_syn_data and get_metadata_file:
                    extracted_data = extract_syn(data_conf_filter=data_conf_filter, data=raw_supplementary_data)


                extensions_metadata = {**extracted_data, **extensions_metadata}
                extensions_metadata['is_supplementary_data_included_eda_ext_b'] = True
                is_supplementary_data_successful = True
                is_supplementary_file_missing = False
            else:
                extensions_metadata['is_supplementary_data_included_eda_ext_b'] = False
                is_supplementary_data_successful = False
                is_supplementary_file_missing = True
        else:
            extensions_metadata['is_supplementary_data_included_eda_ext_b'] = False
            is_supplementary_data_successful = True
            is_supplementary_file_missing = False

        data['extensions'] = extensions_metadata

    except (Exception, psycopg2.Error) as error:
        is_supplementary_data_successful = False
        traceback.print_exc()
        print("Error while fetching data for metadata", error)
    finally:
        # closing database connection.
        if conn:
            if cursor:
                cursor.close()
            conn.close()

    # if os.path.exists(local_supplementary_data):
    #     os.remove(local_supplementary_data)

    return is_supplementary_data_successful, is_supplementary_file_missing, metadata_type, data
