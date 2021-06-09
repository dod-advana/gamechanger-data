from dataPipelines.gc_eda_pipeline.conf import Conf
from dataPipelines.gc_eda_pipeline.indexer.eda_indexer import EDSConfiguredElasticsearchPublisher
from dataPipelines.gc_eda_pipeline.metadata.metadata_json_simple import metadata_extraction
from dataPipelines.gc_eda_pipeline.audit.audit import audit_record_new
import time
import json


def generate_metadata_data(staging_folder: str, data_conf_filter: dict, file: str, filename: str,
                           aws_s3_output_pdf_prefix: str, audit_id: str, audit_rec: dict,
                           publish_audit: EDSConfiguredElasticsearchPublisher):

    md_file_local_path = staging_folder + "/pdf/" + file + ".metadata"
    md_file_s3_path = aws_s3_output_pdf_prefix + "/" + file + ".metadata"

    pds_start = time.time()

    is_md_successful, is_supplementary_file_missing, md_type, md_data = metadata_extraction(staging_folder, file, data_conf_filter, aws_s3_output_pdf_prefix, skip_metadata)

    # with open(md_file_local_path, "w") as output_file:
    #     json.dump(md_data, output_file)

    # Conf.s3_utils.upload_file(file=md_file_local_path, object_name=md_file_s3_path)
    pds_end = time.time()
    time_md = pds_end - pds_start

    audit_rec.update({"filename_s": filename, "eda_path_s": file, "metadata_path_s": md_file_s3_path,
                      "metadata_type_s": md_type, "is_metadata_suc_b": is_md_successful,
                      "is_supplementary_file_missing": is_supplementary_file_missing,
                      "metadata_time_f": round(time_md, 4), "modified_date_dt": int(time.time())})
    audit_record_new(audit_id=audit_id, publisher=publish_audit, audit_record=audit_rec)

    return md_file_s3_path, md_file_local_path, md_data


def generate_metadata_file(staging_folder: str, data_conf_filter: dict, file: str, filename: str,
                           aws_s3_output_pdf_prefix: str, audit_id: str, audit_rec: dict,
                           publish_audit: EDSConfiguredElasticsearchPublisher):

    md_file_local_path = staging_folder + "/pdf/" + file + ".metadata"
    md_file_s3_path = aws_s3_output_pdf_prefix + "/" + file + ".metadata"

    pds_start = time.time()

    is_md_successful, is_supplementary_file_missing, md_type, data = metadata_extraction(staging_folder, file, data_conf_filter, aws_s3_output_pdf_prefix)

    with open(md_file_local_path, "w") as output_file:
        json.dump(data, output_file)

    # Conf.s3_utils.upload_file(file=md_file_local_path, object_name=md_file_s3_path)
    pds_end = time.time()
    time_md = pds_end - pds_start

    audit_rec.update({"filename_s": filename, "eda_path_s": file, "metadata_path_s": md_file_s3_path,
                      "metadata_type_s": md_type, "is_metadata_suc_b": is_md_successful,
                      "is_supplementary_file_missing": is_supplementary_file_missing,
                      "metadata_time_f": round(time_md, 4), "modified_date_dt": int(time.time())})
    audit_record_new(audit_id=audit_id, publisher=publish_audit, audit_record=audit_rec)

    return md_file_s3_path, md_file_local_path
