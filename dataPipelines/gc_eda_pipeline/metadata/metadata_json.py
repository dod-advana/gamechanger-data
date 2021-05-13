import psycopg2
from psycopg2.extras import RealDictCursor
import os
import json
from datetime import datetime
from dataPipelines.gc_eda_pipeline.conf import Conf
from typing import Union
from pathlib import Path
import traceback
from dataPipelines.gc_eda_pipeline.metadata.metadata_util import title


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

    aws_s3_syn_json = data_conf_filter['eda']['aws_s3_syn_json']
    aws_s3_pds_json = data_conf_filter['eda']['aws_s3_pds_json']

    sql_check_if_syn_metadata_exist = data_conf_filter['eda']['sql_check_if_syn_metadata_exist']
    sql_check_if_pds_metadata_exist = data_conf_filter['eda']['sql_check_if_pds_metadata_exist']

    global date_fields_l
    date_fields_l = data_conf_filter['eda']['sql_filter_fields']['date']
    supplementary_s3_post_filter_l = data_conf_filter['eda']['supplementary_s3_post_filter']
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
        local_supplementary_data = ""
        metadata_filename = ""
        ordernum_metadata = ""
        contract_contact_metadata = ""
        contact_metadata = ""
        local_supplementary_data = ""
        category_metadata = ""

        # Check if file has metadata from PDS
        cursor.execute(sql_check_if_pds_metadata_exist, (filename,))
        is_pds_metadata = cursor.fetchone()

        if is_pds_metadata is not None:
            # Get General PDS Metadata
            for col_name in [desc[0] for desc in cursor.description]:
                if is_pds_metadata[col_name] is not None:
                    val = is_pds_metadata[col_name]
                    if col_name in date_fields_l and val is not None and val is not '':
                        result_date = try_parsing_date(val)
                        extensions_metadata[col_name + postfix_es + "_dt"] = result_date
                    else:
                        extensions_metadata[col_name + postfix_es] = val

            if is_pds_metadata['pds_filename'] is not None and is_pds_metadata['pds_filename'] is not '':
                is_pds_data = True
                is_syn_data = False
                metadata_type = "pds"
                metadata_filename = is_pds_metadata['pds_filename']
                contact_metadata = is_pds_metadata['pds_contract']
                ordernum_metadata = is_pds_metadata['pds_ordernum']
                category_metadata = is_pds_metadata['pds_category']
                grouping_metadata = is_pds_metadata['pds_grouping']
                for post_remove in supplementary_s3_post_filter_l:
                    grouping_metadata = grouping_metadata.replace(post_remove, '')

        if not is_pds_data:
            # Check if file has metadata from SYN
            cursor.execute(sql_check_if_syn_metadata_exist, (filename,))
            is_syn_metadata = cursor.fetchone()
            if is_syn_metadata is not None:
                # Get General SYN Metadata
                for col_name in [desc[0] for desc in cursor.description]:
                    if is_syn_metadata[col_name] is not None:
                        extensions_metadata[col_name + postfix_es] = is_syn_metadata[col_name]
                if is_syn_metadata['syn_filename'] is not None:
                    is_pds_data = False
                    is_syn_data = True
                    metadata_type = "syn"
                    metadata_filename = is_syn_metadata['syn_filename']
                    contact_metadata = is_syn_metadata['syn_contract']
                    ordernum_metadata = is_syn_metadata['syn_ordernum']
                    category_metadata = is_syn_metadata['syn_category']
                    grouping_metadata = is_syn_metadata['syn_grouping']
                    for post_remove in supplementary_s3_post_filter_l:
                        grouping_metadata = grouping_metadata.replace(post_remove, '')
            else:
                is_pds_data = False
                is_syn_data = False
                metadata_type = "none"

        extensions_metadata["metadata_type" + postfix_es] = metadata_type
        extensions_metadata['dir_location_eda_ext'] = path
        extensions_metadata['file_location_eda_ext'] = aws_s3_output_pdf_prefix + "/" + filename_input
        data['doc_title'] = title(filename_without_ext)

        if is_syn_data or is_pds_data:
            category_metadata = category_metadata.replace("'", "")
            if ordernum_metadata is not None and ordernum_metadata != "empty" and ordernum_metadata != "":
                contract_contact_metadata = contact_metadata + ordernum_metadata
            else:
                contract_contact_metadata = contact_metadata

        if is_pds_data:
            # Download File from S3
            local_supplementary_data = staging_folder + "/supplementary_data/" + metadata_filename
            if operating_environment == "dev":
                s3_supplementary_data = aws_s3_pds_json + contract_contact_metadata + "/" + metadata_filename
            else:
                s3_supplementary_data = aws_s3_pds_json + category_metadata + "/" + grouping_metadata + "/" + contract_contact_metadata + "/" + metadata_filename

        if is_syn_data:
            # Download File from S3
            local_supplementary_data = staging_folder + "/supplementary_data/" + metadata_filename
            if operating_environment == "dev":
                s3_supplementary_data = aws_s3_syn_json + contract_contact_metadata + "/" + metadata_filename
            else:
                s3_supplementary_data = aws_s3_syn_json + category_metadata + "/" + grouping_metadata + "/" + contract_contact_metadata + "/" + metadata_filename

        if is_pds_data or is_syn_data:
            if Conf.s3_utils.object_exists(object_path=s3_supplementary_data):
                Conf.s3_utils.download_file(file=local_supplementary_data, object_path=s3_supplementary_data)
                with open(local_supplementary_data) as f:
                    supplementary_data = json.load(f)
                    format_supplementary_data(supplementary_data)
                    extensions_metadata = {**supplementary_data, **extensions_metadata}
                    extensions_metadata['is_supplementary_data_included_eda_ext_b'] = True
                    is_supplementary_data_successful = True
                    is_supplementary_file_missing = False
            else:
                extensions_metadata['is_supplementary_data_included_eda_ext_b'] = False
                is_supplementary_data_successful = False
                is_supplementary_file_missing = True
        else:
            extensions_metadata['is_supplementary_data_included_eda_ext_b'] = True
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

    if os.path.exists(local_supplementary_data):
        os.remove(local_supplementary_data)

    return is_supplementary_data_successful, is_supplementary_file_missing, metadata_type, data


def read_extension_conf() -> dict:
    ext_app_config_name = os.environ.get("GC_APP_CONFIG_EXT_NAME")
    with open(ext_app_config_name) as json_file:
        data = json.load(json_file)
    return data


def try_parsing_date(text) -> int:
    for fmt in ('%Y-%m-%d', '%Y%m%d'):
        try:
            # datetime.strptime(text, "%Y-%m-%d")
            # return text
            return int(datetime.strptime(text, fmt).timestamp())
        except ValueError:
            pass
    return 0


def format_supplementary_data(json_info):
    if isinstance(json_info, dict):
        for key in list(json_info.keys()):
            value = json_info[key]
            if isinstance(json_info[key], list):
                append = "_eda_ext_n"
            elif isinstance(json_info[key], dict):
                append = "_eda_ext_n"
            else:
                key_lower = key.lower()
                val = json_info[key]
                if key_lower in date_fields_l and val is not None:
                    append = "_eda_ext_dt"
                    value = try_parsing_date(val)
                    if value < 0:
                        value = None
                else:
                    append = "_eda_ext"
                    value = val

            # Elasticsearch epoch_millis does not allow neg num
            if value is not None:
                key_lower = key.lower() + append
                json_info[key_lower] = value

            if append == "_eda_ext_dt":
                key_lower_other = key.lower() + "_eda_ext_date_only"
                json_info[key_lower_other] = val

            del json_info[key]
            format_supplementary_data(json_info[key_lower])

    elif isinstance(json_info, list):
        for item in json_info:
            format_supplementary_data(item)
