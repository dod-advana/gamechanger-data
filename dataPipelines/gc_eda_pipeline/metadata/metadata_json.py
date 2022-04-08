import os
import json
from datetime import datetime
from dataPipelines.gc_eda_pipeline.conf import Conf
import traceback
from dataPipelines.gc_eda_pipeline.metadata.pds_extract_json import extract_pds
from dataPipelines.gc_eda_pipeline.metadata.syn_extract_json import extract_syn
from dataPipelines.gc_eda_pipeline.metadata.metadata_util import title, mod_identifier
from dataPipelines.gc_eda_pipeline.metadata.fpds_ng import fpds_ng

from urllib3.exceptions import ProtocolError
import time
from psycopg2.pool import ThreadedConnectionPool


def metadata_extraction(filename_input: str, data_conf_filter: dict,
                        aws_s3_output_pdf_prefix: str, db_pool: ThreadedConnectionPool):

    postfix_es = data_conf_filter['eda']['postfix_es']

    path, filename = os.path.split(filename_input)
    filename_without_ext, file_extension = os.path.splitext(filename)
    data = {"access_timestamp": str(datetime.now()), 'doc_name': filename_without_ext,
            'doc_title': title(filename_without_ext), 'title': title(filename_without_ext),
            "mod_identifier_eda_ext": mod_identifier(filename_without_ext)}
    extensions_metadata = {}

    is_supplementary_file_missing = False

    sql_check_if_syn_metadata_exist = data_conf_filter['eda']['sql_check_if_syn_metadata_exist']
    sql_check_if_pds_metadata_exist = data_conf_filter['eda']['sql_check_if_pds_metadata_exist']

    date_fields_l = data_conf_filter['eda']['sql_filter_fields']['date']
    operating_environment = data_conf_filter['eda']['operating_environment']

    metadata_type = "none"

    try:
        is_pds_data = False
        is_syn_data = False
        is_fpds_data = False
        metadata_type = "none"
        s3_supplementary_data = ""
        metadata_filename = ""
        s3_location = ""

        # Check if file has metadata from PDS
        conn = db_pool.getconn()
        cursor = conn.cursor()
        cursor.execute(sql_check_if_pds_metadata_exist, (filename,))
        is_pds_metadata = cursor.fetchone()
        db_pool.putconn(conn)


        # is_pds_metadata = db_pool.fetchone_sql(sql_check_if_pds_metadata_exist, (filename,))

        if is_pds_metadata is not None:
            data = dict(is_pds_metadata)
            # print(data)
            # Get General PDS Metadata
            for col_name, val in data.items():
                # print(col_name, '->', val)
                if col_name in date_fields_l and val is not None and val is not '':
                    extensions_metadata[col_name + postfix_es + "_dt"] = val
                else:
                    extensions_metadata[col_name + postfix_es] = val

            if extensions_metadata.get('pds_json_filename' + postfix_es):
                is_pds_data = True
                is_syn_data = False
                metadata_type = "pds"
                metadata_filename = extensions_metadata.get('pds_json_filename' + postfix_es)
                s3_location = extensions_metadata.get('s3_loc' + postfix_es)

        if not is_pds_data:
            # Check if file has metadata from SYN
            conn = db_pool.getconn()
            cursor = conn.cursor()
            cursor.execute(sql_check_if_syn_metadata_exist, (filename,))
            is_syn_metadata = cursor.fetchone()
            db_pool.putconn(conn)

            is_syn_metadata = db_pool.fetchone_sql(sql_check_if_syn_metadata_exist, (filename,))



            if is_syn_metadata is not None:
                data = dict(is_syn_metadata)
                for col_name, val in data.items():
                    if col_name in date_fields_l and val is not None and val is not '':
                        extensions_metadata[col_name + postfix_es + "_dt"] = val
                    else:
                        extensions_metadata[col_name + postfix_es] = val
                if extensions_metadata.get('syn_json_filename' + postfix_es):
                    is_pds_data = False
                    is_syn_data = True
                    metadata_type = "syn"
                    metadata_filename = extensions_metadata.get('syn_json_filename' + postfix_es)
                    s3_location = extensions_metadata.get('s3_loc'+ postfix_es)
            else:
                is_pds_data = False
                is_syn_data = False
                metadata_type = "none"
        # db_pool.close_all()

        extensions_metadata["metadata_type" + postfix_es] = metadata_type
        extensions_metadata['dir_location_eda_ext'] = path
        extensions_metadata['file_location_eda_ext'] = aws_s3_output_pdf_prefix + "/" + filename_input
        data['doc_title'] = title(filename_without_ext)

        if is_pds_data:
            # Download File from S3
            s3_location = s3_location.strip()
            if operating_environment == "dev":
                s3_supplementary_data = s3_location.replace("s3://advana-data-zone/", "")
            else:
                s3_supplementary_data = s3_location.replace("s3://advana-eda-wawf-restricted/", "")

        if is_syn_data:
            # Download File from S3
            s3_location = s3_location.strip()
            if operating_environment == "dev":
                s3_supplementary_data = s3_location.replace("s3://advana-data-zone/", "")
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

                if is_pds_data and get_metadata_file:
                    extracted_data = extract_pds(data_conf_filter=data_conf_filter, data=raw_supplementary_data,
                                                 extensions_metadata=extensions_metadata, db_pool=db_pool)

                if is_syn_data and get_metadata_file:
                    extracted_data = extract_syn(data_conf_filter=data_conf_filter, data=raw_supplementary_data,  db_pool=db_pool)

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

        # print(filename)
        fpds_data = fpds_ng(filename)
        # print("-------")
        # print(type(extensions_metadata))
        # print(fpds_data)
        # print(json.dumps(fpds_data, indent=2))
        # print("-------")
        # print(json.loads(temp))

        if fpds_data is not None and len(fpds_data) > 0:
            is_fpds_data = True
            extensions_metadata['fpds_ng_n'] = fpds_data
        data['extensions'] = extensions_metadata

    except Exception as error:
        is_supplementary_data_successful = False
        traceback.print_exc()
        print("Error while fetching data for metadata", error)
    # finally:
    #     # closing database connection.
    #     if conn:
    #         if cursor:
    #             cursor.close()
    #         conn.close()

    return is_supplementary_data_successful, is_supplementary_file_missing, metadata_type, is_pds_data, is_syn_data, is_fpds_data, data
