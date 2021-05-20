from dataPipelines.gc_eda_pipeline.indexer.eda_indexer import EDSConfiguredElasticsearchPublisher
from dataPipelines.gc_eda_pipeline.audit.audit import audit_record_new
import time
import json


def index(publish_es: EDSConfiguredElasticsearchPublisher, staging_folder: str, md_file_local_path: str,
          ex_file_local_path: str, path: str, filename_without_ext: str, ex_file_s3_path: str, audit_id: str,
          audit_rec: dict, publish_audit: EDSConfiguredElasticsearchPublisher):

    index_start = time.time()

    with open(md_file_local_path) as metadata_file:
        metadata_file_data = json.load(metadata_file)

    with open(ex_file_local_path) as parsed_pdf_file:
        parsed_pdf_file_data = json.load(parsed_pdf_file)

    if 'extensions' in metadata_file_data.keys():
        extensions_json = metadata_file_data["extensions"]
        parsed_pdf_file_data = {**parsed_pdf_file_data, **extensions_json}
        del metadata_file_data['extensions']

    index_json_data = {**parsed_pdf_file_data, **metadata_file_data}

    index_output_file_path = staging_folder + "/index/" + path + "/" + filename_without_ext + ".index.json"
    with open(index_output_file_path, "w") as output_file:
        json.dump(index_json_data, output_file)

    is_index = publish_es.index_json(index_output_file_path, ex_file_s3_path)
    index_end = time.time()
    time_index = index_end - index_start

    audit_rec.update({"is_index_b": is_index, "index_time_f": round(time_index, 4),
                      "modified_date_dt": int(time.time())})
    audit_record_new(audit_id=audit_id, publisher=publish_audit, audit_record=audit_rec)
    return index_output_file_path
