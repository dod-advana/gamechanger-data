from dataPipelines.gc_eda_pipeline.indexer.eda_indexer import EDSConfiguredElasticsearchPublisher
from dataPipelines.gc_eda_pipeline.metadata.metadata_json import metadata_extraction
from dataPipelines.gc_eda_pipeline.audit.audit import audit_record_new
import time


def generate_metadata_data(staging_folder: str, data_conf_filter: dict, file: str, filename: str,
                           aws_s3_output_pdf_prefix: str, audit_id: str, audit_rec: dict,
                           publish_audit: EDSConfiguredElasticsearchPublisher):

    pds_start = time.time()

    is_md_successful, is_supplementary_file_missing, md_type, md_data = metadata_extraction(staging_folder, file, data_conf_filter, aws_s3_output_pdf_prefix)

    pds_end = time.time()
    time_md = pds_end - pds_start

    audit_rec.update({"filename_s": filename, "eda_path_s": file,
                      "metadata_type_s": md_type, "is_metadata_suc_b": is_md_successful,
                      "is_supplementary_file_missing": is_supplementary_file_missing,
                      "metadata_time_f": round(time_md, 4), "modified_date_dt": int(time.time())})
    audit_record_new(audit_id=audit_id, publisher=publish_audit, audit_record=audit_rec)

    return md_data

