from dataPipelines.gc_eda_pipeline.indexer.eda_indexer import EDSConfiguredElasticsearchPublisher
import time
import hashlib
import json


def create_index(index_name: str, alias: str, ingest_dir=""):
    publisher = EDSConfiguredElasticsearchPublisher(index_name=index_name, ingest_dir=ingest_dir,  alias=alias)
    publisher.create_index()
    if alias:
        publisher.update_alias()
    return publisher


def get_es_publisher(staging_folder: str, index_name: str, alias: str) -> EDSConfiguredElasticsearchPublisher:
    publisher = EDSConfiguredElasticsearchPublisher(index_name=index_name, ingest_dir=staging_folder, alias=alias)
    return publisher


def index_data_file(staging_folder: str, index_file_local_path: str,  metadata_file_data: str, parsed_pdf_file_data: str,
               ex_file_s3_path: str, audit_rec: dict):

    if 'extensions' in metadata_file_data.keys():
        extensions_json = metadata_file_data["extensions"]
        parsed_pdf_file_data = {**parsed_pdf_file_data, **extensions_json}
        del metadata_file_data['extensions']

    index_json_data = {**parsed_pdf_file_data, **metadata_file_data}

    index_json_data["_id"] = hashlib.sha256(ex_file_s3_path.encode()).hexdigest()
    # is_index = publish_es.index_data(index_json_data, ex_file_s3_path)

    with open(staging_folder + "/index/" + index_file_local_path, "w") as output_file:
        json.dump(index_json_data, output_file)

    audit_rec.update({"modified_date_dt": int(time.time())})
