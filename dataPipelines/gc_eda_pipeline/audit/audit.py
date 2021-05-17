from dataPipelines.gc_eda_pipeline.indexer.eda_indexer import EDSConfiguredElasticsearchPublisher

def create_index(index_name: str, alias: str):
    publisher = EDSConfiguredElasticsearchPublisher(index_name=index_name, ingest_dir="",  alias=alias)
    publisher.create_index()
    if alias:
        publisher.update_alias()
    return publisher


def get_es_publisher(staging_folder: str, index_name: str, alias: str) -> EDSConfiguredElasticsearchPublisher:
    publisher = EDSConfiguredElasticsearchPublisher(index_name=index_name, ingest_dir=staging_folder,
                                                 alias=alias)
    return publisher


def audit_record_new(audit_id: str, publisher: EDSConfiguredElasticsearchPublisher, audit_record: dict):
    publisher.insert_record(id_record=audit_id, json_record=audit_record)


def audit_complete(audit_id: str, publisher: EDSConfiguredElasticsearchPublisher, directory: str, number_of_files: int,
                   number_file_failed: int, modified_date: int, duration: int):
    ar = {
        "completed": "completed",
        "directory_s": directory,
        "number_of_files_l": number_of_files,
        "number_file_failed_l": number_file_failed,
        "modified_date_dt": modified_date,
        "duration_l": duration
    }
    publisher.insert_record(id_record=audit_id, json_record=ar)