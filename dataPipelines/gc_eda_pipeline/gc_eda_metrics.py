import click
import json
import os
from dataPipelines.gc_elasticsearch_publisher.gc_elasticsearch_publisher import ConfiguredElasticsearchPublisher
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


def read_extension_conf() -> dict:
    ext_app_config_name = os.environ.get("GC_APP_CONFIG_EXT_NAME")
    with open(ext_app_config_name) as json_file:
        data = json.load(json_file)
    return data


def get_es_publisher(staging_folder: str, index_name: str, alias: str) -> ConfiguredElasticsearchPublisher:
    publisher = ConfiguredElasticsearchPublisher(index_name=index_name, ingest_dir=staging_folder,
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
