import json
import os
import time

import click
import psycopg2
from psycopg2.extras import RealDictCursor

from dataPipelines.gc_eda_pipeline.indexer.eda_indexer import EDSConfiguredElasticsearchPublisher
from dataPipelines.gc_eda_pipeline.utils.eda_utils import read_extension_conf

data_conf_filter = read_extension_conf()

@click.command()
@click.option(
    '-s',
    '--staging-folder',
    help="A temp folder for which the eda data will be staged for processing.",
    required=True,
    type=str,
)
def run(staging_folder: str):
    data_conf_filter = read_extension_conf()

    db_data = []
    db_failed_data = []
    # l_filenames = []
    l_filenames_dic = {}

    start_time = time.time()

    # Init Elasticsearch instance
    print(data_conf_filter['eda']['audit_index'])
    publish_audit = get_es_publisher(staging_folder=staging_folder, index_name=data_conf_filter['eda']['audit_index'],
                                     alias=data_conf_filter['eda']['audit_index'])
    index = data_conf_filter['eda']['audit_index']
    es = publish_audit.es

    body = {
        "track_total_hits": True,
        "_source": ["filename_s", "eda_path_s", "gc_path_s", "json_path_s", "metadata_type_s", "is_metadata_suc_b", "is_ocr_b",
                    "is_docparser_b", "is_index_b", "modified_date_dt", "is_supplementary_file_missing"],
        "query": {
            "match_all": {}
        }
    }

    # Check index exists
    if not es.indices.exists(index=index):
        print("Index " + index + " not exists")
        exit()
    #
    # Init scroll by search
    data = es.search(
        index=index,
        scroll='5m',
        size=1000,
        body=body
    )

    # Get the scroll ID
    sid = data['_scroll_id']
    scroll_size = len(data['hits']['hits'])

    counter = scroll_size
    so_far_processed = 0
    while scroll_size > 0:
        "Scrolling..."

        # Before scroll, process current batch of hits
        for item in data['hits']['hits']:
            source = item['_source']

            if source.get('filename_s'):
                base_path, filename = os.path.split(source.get('eda_path_s'))
                filename_without_ext, file_extension = os.path.splitext(filename)

                if source.get("is_index_b"):

                    if find_filename_in_dict(l_filenames_dic, source.get('filename_s')):
                    # if source.get('filename_s') in l_filenames:
                        data_value_failed = {'filename': source.get('filename_s'),
                                             'base_path': base_path,
                                             'reason': "File is a dup",
                                             'modified_date_dt': source.get("modified_date_dt")}
                        db_failed_data.append(data_value_failed)
                    else:
                        data_value = {'filename': source.get('filename_s'),
                                      'base_path': base_path,
                                      'eda_path': source.get('eda_path_s'),
                                      'gc_path': source.get('gc_path_s'),
                                      'json_path': source.get('json_path_s'),
                                      'metadata_type': source.get("metadata_type_s"),
                                      'is_metadata_suc': source.get("is_metadata_suc_b"),
                                      'is_ocr': source.get("is_ocr_b"),
                                      'is_docparser': source.get("is_docparser_b"),
                                      'is_index': source.get("is_index_b"),
                                      'is_supplementary_file_missing': source.get("is_supplementary_file_missing"),
                                      'modified_date_dt': source.get("modified_date_dt")
                                      }
                        # l_filenames.append(source.get('filename_s'))
                        l_filenames_dic[source.get('filename_s')] = True
                        db_data.append(data_value)
                else:
                    reason = "File might be corrupted"
                    if file_extension != ".pdf":
                        reason = "File is not pdf"

                    data_value_failed = {'filename': source.get('filename_s'),
                                         'base_path': base_path,
                                         'reason': reason,
                                         'modified_date_dt': source.get("modified_date_dt")
                    }
                    db_failed_data.append(data_value_failed)

                if len(db_data) > 10000:
                    so_far_processed = so_far_processed + len(db_data)
                    print(f"So Far Processed : {so_far_processed}")
                    migrate_audit_success_data(db_data)
                    migrate_audit_failed_data(db_failed_data)
                    db_data = []
                    db_failed_data = []

        data = es.scroll(scroll_id=sid, scroll='5m')

        # Update the scroll ID
        sid = data['_scroll_id']

        # Get the number of results that returned in the last scroll
        scroll_size = len(data['hits']['hits'])
        counter = counter + scroll_size
        # print(counter)

    # print the elapsed time
    # print(f"data_value: {len(db_data)}")
    # print(f"db_file_data: {len(db_failed_data)}")

    so_far_processed = so_far_processed + len(db_data)
    print(f"Processed : {so_far_processed}")
    migrate_audit_success_data(db_data)
    migrate_audit_failed_data(db_failed_data)

    print("TOTAL TIME:", time.time() - start_time, "seconds.")


def get_es_publisher(staging_folder: str, index_name: str, alias: str) -> EDSConfiguredElasticsearchPublisher:
    publisher = EDSConfiguredElasticsearchPublisher(index_name=index_name, ingest_dir=staging_folder,
                                                    alias=alias)
    return publisher


def migrate_audit_success_data(data: list) -> None:
    conn = psycopg2.connect(host=data_conf_filter['eda']['database']['hostname'],
                            port=data_conf_filter['eda']['database']['port'],
                            user=data_conf_filter['eda']['database']['user'],
                            password=data_conf_filter['eda']['database']['password'],
                            dbname=data_conf_filter['eda']['database']['db'],
                            cursor_factory=psycopg2.extras.DictCursor)
    sql_audit_success = """ INSERT INTO public.gc_file_process_status
    SELECT
        *
    FROM json_populate_recordset(NULL::public.gc_file_process_status, %s) ON CONFLICT (filename) DO NOTHING;
    """

    with conn.cursor() as cursor:
        cursor.execute(sql_audit_success, (json.dumps(data),))
        conn.commit()


def migrate_audit_failed_data(data: list) -> None:
    conn = psycopg2.connect(host=data_conf_filter['eda']['database']['hostname'],
                            port=data_conf_filter['eda']['database']['port'],
                            user=data_conf_filter['eda']['database']['user'],
                            password=data_conf_filter['eda']['database']['password'],
                            dbname=data_conf_filter['eda']['database']['db'],
                            cursor_factory=psycopg2.extras.DictCursor)
    sql_audit_failed = """INSERT INTO public.gc_file_process_fail 
    SELECT 
        *
    FROM json_populate_recordset(NULL::public.gc_file_process_fail, %s) on CONFLICT (filename, base_path) DO NOTHING;
    """
    with conn.cursor() as cursor:
        cursor.execute(sql_audit_failed, (json.dumps(data),))
        conn.commit()


def find_filename_in_dict(dct, filename):
    if filename in dct.keys():
        return True
    else:
        return False

if __name__ == '__main__':
    run()
