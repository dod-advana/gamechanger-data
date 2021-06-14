from dataPipelines.gc_eda_pipeline.indexer.eda_indexer import EDSConfiguredElasticsearchPublisher
from dataPipelines.gc_eda_pipeline.audit.audit import audit_record_new
import time


def create_index(index_name: str, alias: str, ingest_dir=""):
    publisher = EDSConfiguredElasticsearchPublisher(index_name=index_name, ingest_dir=ingest_dir,  alias=alias)
    publisher.create_index()
    if alias:
        publisher.update_alias()
    return publisher


def get_es_publisher(staging_folder: str, index_name: str, alias: str) -> EDSConfiguredElasticsearchPublisher:
    publisher = EDSConfiguredElasticsearchPublisher(index_name=index_name, ingest_dir=staging_folder,
                                                 alias=alias)
    return publisher


def index_data(publish_es: EDSConfiguredElasticsearchPublisher, metadata_file_data: str,
          parsed_pdf_file_data: str, ex_file_s3_path: str, audit_id: str,
          audit_rec: dict, publish_audit: EDSConfiguredElasticsearchPublisher):

    index_start = time.time()

    if 'extensions' in metadata_file_data.keys():
        extensions_json = metadata_file_data["extensions"]
        parsed_pdf_file_data = {**parsed_pdf_file_data, **extensions_json}
        del metadata_file_data['extensions']

    index_json_data = {**parsed_pdf_file_data, **metadata_file_data}

    is_index = publish_es.index_data(index_json_data, ex_file_s3_path)
    index_end = time.time()
    time_index = index_end - index_start

    audit_rec.update({"is_index_b": is_index, "index_time_f": round(time_index, 4),
                      "modified_date_dt": int(time.time())})
    audit_record_new(audit_id=audit_id, publisher=publish_audit, audit_record=audit_rec)