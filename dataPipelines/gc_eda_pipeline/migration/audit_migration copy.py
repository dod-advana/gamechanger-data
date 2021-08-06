import json
import os
import time

import click
import psycopg2
from psycopg2.extras import RealDictCursor

from dataPipelines.gc_eda_pipeline.indexer.eda_indexer import EDSConfiguredElasticsearchPublisher
from dataPipelines.gc_eda_pipeline.utils.eda_utils import read_extension_conf


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
    conn = psycopg2.connect(host=data_conf_filter['eda']['database']['hostname'],
                            port=data_conf_filter['eda']['database']['port'],
                            user=data_conf_filter['eda']['database']['user'],
                            password=data_conf_filter['eda']['database']['password'],
                            dbname=data_conf_filter['eda']['database']['db'],
                            cursor_factory=psycopg2.extras.DictCursor)
    query = """
    INSERT INTO public.gc_file_process_status
    SELECT
        *
    FROM json_populate_recordset(NULL::public.gc_file_process_status, %s) ON CONFLICT (filename) DO NOTHING;
    """
    db_data = []
    start_time = time.time()
    # Init Elasticsearch instance

    print(data_conf_filter['eda']['audit_index'])
    publish_audit = get_es_publisher(staging_folder=staging_folder, index_name=data_conf_filter['eda']['audit_index'],
                                     alias=data_conf_filter['eda']['audit_index'])
    index = data_conf_filter['eda']['audit_index']
    es = publish_audit.es


    body = {
        "query": {
            "match_all": {}
        }
    }
    # Process hits here
    # def process_hits(hits):
    #     for item in hits:
    #         print(json.dumps(item, indent=2))

    # Check index exists
    if not es.indices.exists(index=index):
        print("Index " + index + " not exists")
        exit()
    #
    # Init scroll by search
    data = es.search(
        index=index,
        scroll='2m',
        size=10000,
        body=body
    )

    # Get the scroll ID
    sid = data['_scroll_id']
    scroll_size = len(data['hits']['hits'])

    counter = scroll_size
    while scroll_size > 0:
        "Scrolling..."

        # Before scroll, process current batch of hits
        # process_hits(data['hits']['hits'])
        for item in data['hits']['hits']:
            source = item['_source']

            if source.get('filename_s'):
                base_path, filename = os.path.split(source.get('eda_path_s'))
                filename_without_ext, file_extension = os.path.splitext(filename)
                # print(base_path)
                # print(filename)

                filename_s = source.get('filename_s')
                eda_path_s = source.get('eda_path_s')
                gc_path_s = source.get('gc_path_s')
                json_path_s = source.get('json_path_s')
                is_ocr_b = source.get('is_ocr_b')

                data_value = {'filename': filename_s, 'base_path': base_path, 'eda_path': eda_path_s, 'gc_path': gc_path_s, 'json_path': json_path_s, 'is_ocr': is_ocr_b}
                # print(data_value)
                db_data.append(data_value)


            # print(source)
            # print(json.dumps(item, indent=2))
            # exit()

        # if db_data:
        #     cursor = conn.cursor()
        #     cursor.execute(query, (json.dumps(db_data),))
        #     conn.commit()
        # db_data = []

        data = es.scroll(scroll_id=sid, scroll='2m')

        # Update the scroll ID
        sid = data['_scroll_id']

        # Get the number of results that returned in the last scroll
        scroll_size = len(data['hits']['hits'])
        counter = counter + scroll_size
        print(counter)

    # print the elapsed time
    print(f"data_value: {len(db_data)}")
    # print(db_data)


    cursor = conn.cursor()
    cursor.execute(query, (json.dumps(db_data),))
    conn.commit()

    print("TOTAL TIME:", time.time() - start_time, "seconds.")


def get_es_publisher(staging_folder: str, index_name: str, alias: str) -> EDSConfiguredElasticsearchPublisher:
    publisher = EDSConfiguredElasticsearchPublisher(index_name=index_name, ingest_dir=staging_folder,
                                                    alias=alias)
    return publisher


if __name__ == '__main__':
    run()
