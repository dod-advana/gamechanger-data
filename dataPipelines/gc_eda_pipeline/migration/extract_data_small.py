########################################################################################################################
#                                                                                                                      #
#                                   Deprecated Code                                                                    #
#                                                                                                                      #
########################################################################################################################
# import json
# import os
# import time
#
# import click
# import psycopg2
# from psycopg2.extras import RealDictCursor
#
# from dataPipelines.gc_eda_pipeline.indexer.eda_indexer import EDSConfiguredElasticsearchPublisher
# from dataPipelines.gc_eda_pipeline.utils.eda_utils import read_extension_conf
#
# data_conf_filter = read_extension_conf()
#
# @click.command()
# @click.option(
#     '-s',
#     '--staging-folder',
#     help="A temp folder for which the eda data will be staged for processing.",
#     required=True,
#     type=str,
# )
# def run(staging_folder: str):
#     data_conf_filter = read_extension_conf()
#
#     db_data = []
#     db_failed_data = []
#     l_filenames = []
#
#     start_time = time.time()
#
#     # Init Elasticsearch instance
#     print(data_conf_filter['eda']['eda_index'])
#     publish_audit = get_es_publisher(staging_folder=staging_folder, index_name=data_conf_filter['eda']['eda_index'],
#                                      alias=data_conf_filter['eda']['eda_index_alias'])
#     index = data_conf_filter['eda']['eda_index']
#     es = publish_audit.es
#
#     body = {
#     "_source": {
#         "includes": [
#             "extracted_data_eda_n.contract_payment_office_dodaac_eda_ext",
#             "extracted_data_eda_n.contract_payment_office_name_eda_ext"
#         ]
#     },
#     "track_total_hits": "true",
#     "query": {
#         "bool": {
#             "filter": [
#                 {
#                     "nested": {
#                         "path": "extracted_data_eda_n",
#                         "query": {
#                             "bool": {
#                                 "should": [
#                                     {
#                                         "range": {
#                                             "extracted_data_eda_n.signature_date_eda_ext_dt": {
#                                                 "gte": "2020",
#                                                 "lte": "2021",
#                                                 "format": "yyyy"
#                                             }
#                                         }
#                                     }
#                                 ]
#                             }
#                         }
#                     }
#                 },
#                 {
#                     "match": {
#                         "mod_identifier_eda_ext": "base_award"
#                     }
#                 }
#             ]
#         }
#     }
# }
#
#     # Check index exists
#     if not es.indices.exists(index=index):
#         print("Index " + index + " not exists")
#         exit()
#     #
#     # Init scroll by search
#     data = es.search(
#         index=index,
#         scroll='2m',
#         size=10000,
#         body=body
#     )
#
#     # Get the scroll ID
#     sid = data['_scroll_id']
#     scroll_size = len(data['hits']['hits'])
#     f = open("small_output.txt", "w+")
#     counter = scroll_size
#     while scroll_size > 0:
#         "Scrolling..."
#
#         # Before scroll, process current batch of hits
#         for item in data['hits']['hits']:
#             source = item['_source']
#             # print(json.dumps(es_data, sort_keys=True))
#             f.write(json.dumps(source, sort_keys=True))
#             f.write("\n")
#
#         data = es.scroll(scroll_id=sid, scroll='2m')
#
#         # Update the scroll ID
#         sid = data['_scroll_id']
#
#         # Get the number of results that returned in the last scroll
#         scroll_size = len(data['hits']['hits'])
#         counter = counter + scroll_size
#         print(counter)
#
#     f.close()
#
#     print("TOTAL TIME:", time.time() - start_time, "seconds.")
#
#
# def get_es_publisher(staging_folder: str, index_name: str, alias: str) -> EDSConfiguredElasticsearchPublisher:
#     publisher = EDSConfiguredElasticsearchPublisher(index_name=index_name, ingest_dir=staging_folder,
#                                                     alias=alias)
#     return publisher
#
# if __name__ == '__main__':
#     run()
