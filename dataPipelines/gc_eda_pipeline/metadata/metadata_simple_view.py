import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dataPipelines.gc_eda_pipeline.metadata.metadata_util import title
from datetime import datetime


def metadata_extraction(staging_folder: str, filename_input: str, data_conf_filter: dict, aws_s3_output_pdf_prefix: str, skip_metadata: bool):
    postfix_es = data_conf_filter['eda']['postfix_es']

    path, filename = os.path.split(filename_input)
    filename_without_ext, file_extension = os.path.splitext(filename)
    data = {"access_timestamp": str(datetime.now()), 'doc_name': filename_without_ext,
            'doc_title': title(filename_without_ext), 'title': title(filename_without_ext)}
    extensions_metadata = {}

    if skip_metadata:
        metadata_type = "skipped"
        extensions_metadata["metadata_type" + postfix_es] = metadata_type
        extensions_metadata['dir_location_eda_ext'] = path
        extensions_metadata['file_location_eda_ext'] = aws_s3_output_pdf_prefix + "/" + filename_input
        data['doc_title'] = title(filename_without_ext)
        is_md_successful = False
        return is_md_successful, metadata_type, data

    # Load Extensions configuration files.
    # data_conf_filter = read_extension_conf()
    max_parallel_workers_per_gather = data_conf_filter['eda']['max_parallel_workers_per_gather']
    work_mem = data_conf_filter['eda']['work_mem']

    sql_check_if_syn_metadata_exist = data_conf_filter['eda']['sql_check_if_syn_metadata_exist']
    sql_syn_header_items_by_given_pdf_filename = data_conf_filter['eda']['sql_syn_header_items_by_given_pdf_filename']
    sql_syn_parsed_vw_syn_contract_card_view = data_conf_filter['eda']['sql_syn_parsed_vw_syn_contract_card_view']

    sql_check_if_pds_metadata_exist = data_conf_filter['eda']['sql_check_if_pds_metadata_exist']
    sql_pds_header_by_given_pdf_filename = data_conf_filter['eda']['sql_pds_header_by_given_pdf_filename']
    sql_pds_parsed_vw_pds_contract_card_view = data_conf_filter['eda']['sql_pds_parsed_vw_pds_contract_card_view']

    date_fields_l = data_conf_filter['eda']['sql_filter_fields']['date']

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

        # setting custom Postgres session values for EDA
        cursor.execute('SET work_mem TO %s', (work_mem,))
        cursor.execute('SET max_parallel_workers_per_gather TO %s', (max_parallel_workers_per_gather,))

        # print("************** Memory ******************")
        cursor.execute('SHOW work_mem')
        # memory = cursor.fetchone()
        cursor.execute('SHOW max_parallel_workers_per_gather')
        # mpwpg = cursor.fetchone()
        # print(f"work_mem {memory}")
        # print(f"max_parallel_workers_per_gather {mpwpg}")
        # print("************** Memory ******************")

        is_pds_data = False
        is_syn_data = False
        metadata_type = "none"
        # Check if file has metadata from PDS
        cursor.execute(sql_check_if_pds_metadata_exist, (filename,))
        # print("************** MetaData PDS ******************")
        # print(cursor.query)
        # print("********************************")
        is_pds_metadata = cursor.fetchone()

        if is_pds_metadata is not None:
            # Get General PDS Metadata
            for col_name in [desc[0] for desc in cursor.description]:
                if is_pds_metadata[col_name] is not None:
                    extensions_metadata[col_name + postfix_es] = is_pds_metadata[col_name]
            if is_pds_metadata['pds_filename'] is not None and is_pds_metadata['pds_filename'] is not '':
                is_pds_data = True
                is_syn_data = False
                metadata_type = "pds"

        if not is_pds_data:
            # Check if file has metadata from SYN
            cursor.execute(sql_check_if_syn_metadata_exist, (filename,))
            # print("************* MetaData SYN *******************")
            # print(cursor.query)
            # print("********************************")
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
            else:
                is_pds_data = False
                is_syn_data = False
                metadata_type = "none"

        extensions_metadata["metadata_type" + postfix_es] = metadata_type
        extensions_metadata['dir_location_eda_ext'] = path
        extensions_metadata['file_location_eda_ext'] = aws_s3_output_pdf_prefix + "/" + filename_input
        data['doc_title'] = title(filename_without_ext)

        if is_syn_data:
            cursor.execute(sql_syn_header_items_by_given_pdf_filename, (filename,))
            # print("************** SYN IDs  ******************")
            # print(cursor.query)
            # print("********************************")
            syn_header_records = cursor.fetchall()
            syn_header_contractids = []
            for syn_header_record in syn_header_records:
                syn_header_contractids.append(syn_header_record[0])

            if len(syn_header_contractids) != 0:
                cursor.execute(sql_syn_parsed_vw_syn_contract_card_view, (tuple(syn_header_contractids),))
                # print("************** SYN Contract ******************")
                # print(cursor.query)
                # print("********************************")
                syn_header_rows = cursor.fetchall()
                syn_header_nodes = []
                for syn_header_row in syn_header_rows:
                    items = {}
                    col_names = [desc[0] for desc in cursor.description]
                    for col in col_names:
                        val = syn_header_row[col]
                        if col in date_fields_l and val is not None:
                            result_date = try_parsing_date(val)
                            items[col + postfix_es + "_dt"] = result_date
                        elif val is not None:
                            items[col + postfix_es] = val
                    syn_header_nodes.append(items)
                extensions_metadata["syn_contract_items" + postfix_es + "_n"] = syn_header_nodes

        if is_pds_data:
            cursor.execute(sql_pds_header_by_given_pdf_filename, (filename,))
            # print("************** PDS IDs ******************")
            # print(cursor.query)
            # print("********************************")
            pds_header_rows = cursor.fetchall()
            pds_header_contractid = []
            for pds_header_row in pds_header_rows:
                pds_header_contractid.append(pds_header_row[0])

            # rowid and dict with col and value (dict inside of a dict)
            if len(pds_header_contractid) != 0:
                cursor.execute(sql_pds_parsed_vw_pds_contract_card_view, (tuple(pds_header_contractid),))
                # print("*********** PDS - Contract ********************")
                # print(cursor.query)
                # print("********************************")
                pds_header_rows = cursor.fetchall()
                pds_header_nodes = []
                for pds_header_row in pds_header_rows:
                    items = {}
                    col_names = [desc[0] for desc in cursor.description]
                    for col in col_names:
                        val = pds_header_row[col]
                        if col in date_fields_l and val is not None:
                            result_date = try_parsing_date(val)
                            items[col + postfix_es + "_dt"] = result_date
                        elif val is not None:
                            items[col + postfix_es] = val
                    pds_header_nodes.append(items)
                extensions_metadata["pds_contract_items" + postfix_es + "_n"] = pds_header_nodes

        data['extensions'] = extensions_metadata
        is_md_successful = True
    except (Exception, psycopg2.Error) as error:
        is_md_successful = False
        print(f"Error while processing {filename_input}", error)
    finally:
        # closing database connection.
        if conn:
            if cursor:
                cursor.close()
            conn.close()
            # print("PostgreSQL connection is closed")

    return is_md_successful, metadata_type, data


def try_parsing_date(text) -> int:
    for fmt in ('%Y-%m-%d', '%Y%m%d'):
        try:
            return int(datetime.strptime(text, fmt).timestamp())
        except ValueError:
            pass
    return 0

