from dataPipelines.gc_eda_pipeline.metadata.metadata_json import metadata_extraction
import time


def generate_metadata_data(data_conf_filter: dict, file: str, filename: str,
                           aws_s3_output_pdf_prefix: str, audit_rec: dict):

    is_md_successful, is_supplementary_file_missing, md_type, md_data = metadata_extraction(file, data_conf_filter,
                                                                                            aws_s3_output_pdf_prefix)

    audit_rec.update({"metadata_type": md_type, "is_metadata_suc": is_md_successful,
                      "is_supplementary_file_missing": is_supplementary_file_missing,
                      "modified_date_dt": int(time.time())})

    return md_data

