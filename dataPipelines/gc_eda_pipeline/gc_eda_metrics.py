import sys

import click
import json
import os
import traceback
import psycopg2
from psycopg2.extras import RealDictCursor

from dataPipelines.gc_eda_pipeline.indexer.eda_indexer import EDSConfiguredElasticsearchPublisher
from dataPipelines.gc_eda_pipeline.utils.eda_utils import read_extension_conf
import csv
from csv import writer

@click.command()
@click.option(
    '-s',
    '--staging-folder',
    help="A temp folder for which the eda data will be staged for processing.",
    required=True,
    type=str,
)
@click.option(
    '--input-list-file',
    required=True,
    type=str
)
@click.option(
    '--output-file',
    required=True,
    type=str
)
def run(staging_folder: str, input_list_file: str, output_file: str):
    print("Starting Gamechanger EDA Metrics Pipeline")
    # Load Extensions configuration files.
    data_conf_filter = read_extension_conf()

    metric_sql = data_conf_filter['eda']['metric_sql']

    try:
        conn = psycopg2.connect(host=data_conf_filter['eda']['database']['hostname'],
                                port=data_conf_filter['eda']['database']['port'],
                                user=data_conf_filter['eda']['database']['user'],
                                password=data_conf_filter['eda']['database']['password'],
                                dbname=data_conf_filter['eda']['database']['db'],
                                cursor_factory=psycopg2.extras.DictCursor)
        cursor = conn.cursor()
        cursor.execute(metric_sql)

        rows = cursor.fetchall()
        s3_prefix = []
        for row in rows:
            s3_prefix.append(row[0])

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

    if len(s3_prefix) == 0:
        print("Something wrong with the query metric table")
        sys.exit()

    directories = []
    with open(input_list_file, "r") as file:
        directories = file.readlines()

    with open(output_file, 'w+', newline='') as outcsv:
        writer = csv.DictWriter(outcsv, fieldnames=["Directory", "Elasticsearch","Files Processed", "OCR", "PDS", "PDS Quarantine", "SYN", "SYN Quarantine", "Failed", "Failed (Text)", "Failed (PDF)"])
        writer.writeheader()

    publish_audit = get_es_publisher(staging_folder=staging_folder, index_name=data_conf_filter['eda']['audit_index'],
                                     alias=data_conf_filter['eda']['audit_index_alias'])

    publish_es = get_es_publisher(staging_folder=staging_folder, index_name=data_conf_filter['eda']['eda_index'],
                                  alias=data_conf_filter['eda']['eda_index_alias'])

    for directory in directories:
        print("\n")
        print(f"-- {directory}")
        # Items in ES
        directory = directory.rstrip()
        query_es_count = {'query': {'bool': {'must': [{'wildcard': {'file_location_eda_ext.keyword': {'value': directory + '*'}}}]}}}
        response_item_in_es = publish_es.count(index=data_conf_filter['eda']['eda_index'], body=query_es_count)
        print("ES Count: : " + str(response_item_in_es['count']))
        item_in_es_count = str(response_item_in_es['count'])

        # Audit number of files processed
        query_files_processed = {'query': {'wildcard': {'gc_path_s': {'value': directory + '*'}}}}
        response_files_processed = publish_audit.count(index=data_conf_filter['eda']['audit_index'], body=query_files_processed)
        print("Processed Count: : " + str(response_files_processed['count']))
        items_processed_count = str(response_files_processed['count'])

        # Audit number of files ocr
        query_ocr_count = {'query': {'bool': {'must': [{'term': {'is_ocr_b': {'value': 'true'}}},{'wildcard': {'gc_path_s': {'value': directory + '*'}}}]}}}
        response_ocr = publish_audit.count(index=data_conf_filter['eda']['audit_index'], body=query_ocr_count)
        print("OCRed: : " + str(response_ocr['count']))
        items_ocred_count = str(response_ocr['count'])

        # files failed to complete processed
        query_failed = {'query': {'bool': {'must': [{'term': {'is_index_b': {'value': 'false'}}},{'wildcard': {'gc_path_s': {'value': directory + '*'}}}]}}}
        response_failed = publish_audit.count(index=data_conf_filter['eda']['audit_index'], body=query_failed)
        print("Failed Count: : " + str(response_failed['count']))
        items_failed_count = str(response_failed['count'])

        # files failed to complete processed (text files)
        query_failed_text = {'query': {'bool': {'must': [{'term': {'is_index_b': {'value': 'false'}}},{'wildcard': {'gc_path_s': {'value': directory + '*.txt'}}}]}}}
        response_failed_text = publish_audit.count(index=data_conf_filter['eda']['audit_index'], body=query_failed_text)
        print("Failed Text Count: : " + str(response_failed_text['count']))
        items_failed_text_count = str(response_failed_text['count'])

        # files failed to complete processed (pdf files)
        query_failed_pdf = {'query': {'bool': {'must': [{'term': {'is_index_b': {'value': 'false'}}},{'wildcard': {'gc_path_s': {'value': directory + '*.pdf'}}}]}}}
        response_failed_pdf = publish_audit.count(index=data_conf_filter['eda']['audit_index'], body=query_failed_pdf)
        print("Failed PDF Count: : " + str(response_failed_pdf['count']))
        items_failed_pdf_count = str(response_failed_pdf['count'])

        # Metadata With PDS data
        query_pds = {'query': {'bool': {'must_not': [{'term': {'completed': {'value': 'completed'}}}],'must': [{'wildcard': {'gc_path_s': {'value': directory + '*'}}},{'term': {'metadata_type_s': {'value': 'pds'}}},{'term': {'is_metadata_suc_b': {'value': 'true'}}},{'term': {'is_supplementary_file_missing': {'value': 'false'}}}]}}}
        response_pds = publish_audit.count(index=data_conf_filter['eda']['audit_index'], body=query_pds)
        print("PDS Count: " + str(response_pds['count']))
        items_pds_count = str(response_pds['count'])

        # Metadata With PDS data quarantine
        query_pds_quarantine = {'query': {'bool': {'must_not': [{'term': {'completed': {'value': 'completed'}}}],'must': [{'wildcard': {'gc_path_s': {'value': directory + '*'}}},{'term': {'metadata_type_s': {'value': 'pds'}}},{'term': {'is_metadata_suc_b': {'value': 'false'}}},{'term': {'is_supplementary_file_missing': {'value': 'true'}}}]}}}
        response_pds_quarantine = publish_audit.count(index=data_conf_filter['eda']['audit_index'], body=query_pds_quarantine)
        print("PDS Quarantine Count: " + str(response_pds_quarantine['count']))
        items_pds_quarantine_count = str(response_pds_quarantine['count'])

        # Metadata With SYN data
        query_syn = {'query': {'bool': {'must_not': [{'term': {'completed': {'value': 'completed'}}}],'must': [{'wildcard': {'gc_path_s': {'value': directory + '*'}}},{'term': {'metadata_type_s': {'value': 'syn'}}},{'term': {'is_metadata_suc_b': {'value': 'true'}}},{'term': {'is_supplementary_file_missing': {'value': 'false'}}}]}}}
        response_syn = publish_audit.count(index=data_conf_filter['eda']['audit_index'], body=query_syn)
        print("SYN Count: " + str(response_syn['count']))
        items_syn_count = str(response_syn['count'])

        # Metadata With SYN data quarantine
        query_syn_quarantine = {'query': {'bool': {'must_not': [{'term': {'completed': {'value': 'completed'}}}],'must': [{'wildcard': {'gc_path_s': {'value': directory + '*'}}},{'term': {'metadata_type_s': {'value': 'syn'}}},{'term': {'is_metadata_suc_b': {'value': 'false'}}},{'term': {'is_supplementary_file_missing': {'value': 'true'}}}]}}}
        response_syn_quarantine = publish_audit.count(index=data_conf_filter['eda']['audit_index'], body=query_syn_quarantine)
        print("SYN Quarantine Count: " + str(response_syn_quarantine['count']))
        items_syn_quarantine_count = str(response_syn_quarantine['count'])

        row_contents = [directory, item_in_es_count, items_processed_count, items_ocred_count,
                        items_pds_count, items_pds_quarantine_count, items_syn_count, items_syn_quarantine_count,
                        items_failed_count, items_failed_text_count, items_failed_pdf_count]

        append_list_as_row(file_name=output_file, list_of_elem=row_contents)


    # Metadata Average Time/Number for OCR
    query_average_time_ocr = {'track_total_hits':'true','size':'0','query':{'bool':{'must_not':[{'term':{'completed':{'value':'completed'}}}],'must':[{'term':{'is_ocr_b':{'value':'true'}}}]}},'aggs':{'number_of_files_ocred':{'value_count':{'field':'is_ocr_b'}},'avg_ocr_time':{'avg':{'field':'ocr_time_f'}}}}
    response_ocr_aggs = publish_audit.search(index=data_conf_filter['eda']['audit_index'], body=query_average_time_ocr)
    print("\n")
    print("Number of files OCR: " + str(response_ocr_aggs['aggregations']['number_of_files_ocred']['value']))
    print("Average Time for OCR: " + str(response_ocr_aggs['aggregations']['avg_ocr_time']['value']))

    # Metadata Average Time/Number for Indexing
    query_average_time_indexer = {'track_total_hits': 'true', 'size': '0', 'query': {'bool': {'must_not': [{'term': {'completed': {'value': 'completed'}}}],'must': [{'term': {'is_index_b': {'value': 'true'}}}]}}, 'aggs': {'number_of_files_index': {'value_count': {'field': 'is_ocr_b'}}, 'avg_index_time': {'avg': {'field': 'ocr_time_f'}}}}
    response_index_aggs = publish_audit.search(index=data_conf_filter['eda']['audit_index'], body=query_average_time_indexer)
    print("\n")
    print("Number of files Index: " + str(response_index_aggs['aggregations']['number_of_files_index']['value']))
    print("Average Time for Indexing: " + str(response_index_aggs['aggregations']['avg_index_time']['value']))

    # Metadata Average Time/Number for Supplementary PDS
    query_average_time_supplementary_pds = {'track_total_hits':'true','size':'0','query':{'bool':{'must_not':[{'term':{'completed':{'value':'completed'}}}],'must':[{'term':{'is_index_b':{'value':'true'}}},{'term':{'is_metadata_suc_b':{'value':'true'}}},{'term':{'is_supplementary_file_missing':{'value':'false'}}},{'term':{'metadata_type_s':{'value':'pds'}}}]}},'aggs':{'number_of_files_metadata_pds':{'value_count':{'field':'metadata_type_s'}},'avg_metadata_time':{'avg':{'field':'metadata_time_f'}}}}
    response_supplementary_pds_aggs = publish_audit.search(index=data_conf_filter['eda']['audit_index'], body=query_average_time_supplementary_pds)
    print("\n")
    print("Number of PDS Files: " + str(response_supplementary_pds_aggs['aggregations']['number_of_files_metadata_pds']['value']))
    print("Average Time for PDS Files: " + str(response_supplementary_pds_aggs['aggregations']['avg_metadata_time']['value']))


    # Metadata Average Time/Number for Supplementary SYN
    query_average_time_supplementary_syn = {'track_total_hits':'true','size':'0','query':{'bool':{'must_not':[{'term':{'completed':{'value':'completed'}}}],'must':[{'term':{'is_index_b':{'value':'true'}}},{'term':{'is_metadata_suc_b':{'value':'true'}}},{'term':{'is_supplementary_file_missing':{'value':'false'}}},{'term':{'metadata_type_s':{'value':'syn'}}}]}},'aggs':{'number_of_files_metadata_syn':{'value_count':{'field':'metadata_type_s'}},'avg_metadata_time':{'avg':{'field':'metadata_time_f'}}}}
    response_supplementary_syn_aggs = publish_audit.search(index=data_conf_filter['eda']['audit_index'], body=query_average_time_supplementary_syn)
    print("\n")
    print("Number of PDS Files: " + str(response_supplementary_syn_aggs['aggregations']['number_of_files_metadata_syn']['value']))
    print("Average Time for PDS Files: " + str(response_supplementary_syn_aggs['aggregations']['avg_metadata_time']['value']))


# def read_extension_conf() -> dict:
#     ext_app_config_name = os.environ.get("GC_APP_CONFIG_EXT_NAME")
#     with open(ext_app_config_name) as json_file:
#         data = json.load(json_file)
#     return data


def get_es_publisher(staging_folder: str, index_name: str, alias: str) -> EDSConfiguredElasticsearchPublisher:
    publisher = EDSConfiguredElasticsearchPublisher(index_name=index_name, ingest_dir=staging_folder,
                                                 alias=alias)
    return publisher


def append_list_as_row(file_name, list_of_elem):
    # Open file in append mode
    with open(file_name, 'a+', newline='') as write_obj:
        # Create a writer object from csv module
        csv_writer = writer(write_obj)
        # Add contents of list as last row in the csv file
        csv_writer.writerow(list_of_elem)


if __name__ == '__main__':
    run()
