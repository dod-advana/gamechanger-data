from dataPipelines.gc_eda_pipeline.indexer.eda_indexer import EDSConfiguredElasticsearchPublisher


def audit_record_new(audit_id: str, publisher: EDSConfiguredElasticsearchPublisher, audit_record: dict):
    publisher.insert_record(id_record=audit_id, json_record=audit_record)


def audit_complete(audit_id: str, publisher: EDSConfiguredElasticsearchPublisher, directory: str, number_of_files: int,
                   number_file_failed: int, modified_date: int, duration: int, bulk_index=0.0):
    ar = {
        "completed": "completed",
        "directory_s": directory,
        "number_of_files_l": number_of_files,
        "number_file_failed_l": number_file_failed,
        "modified_date_dt": modified_date,
        "duration_l": duration,
        "bulk_index_f": bulk_index
    }
    publisher.insert_record(id_record=audit_id, json_record=ar)