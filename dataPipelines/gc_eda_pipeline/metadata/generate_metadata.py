from dataPipelines.gc_eda_pipeline.metadata.metadata_json import metadata_extraction
import time
from dataPipelines.gc_eda_pipeline.database.connection import ConnectionPool

def generate_metadata_data(data_conf_filter: dict, file: str, filename: str,
                           aws_s3_output_pdf_prefix: str, audit_rec: dict, db_pool: ConnectionPool):

    is_supplementary_data_successful, is_supplementary_file_missing, metadata_type, is_pds_data, is_syn_data, is_fpds_data, md_data = metadata_extraction(file, data_conf_filter,
                                                                                            aws_s3_output_pdf_prefix, db_pool)

    audit_rec.update({"is_pds": is_pds_data, "is_syn": is_syn_data,
                      "is_fpds_ng": is_fpds_data,
                      "is_supplementary_file_missing": is_supplementary_file_missing,
                      "modified_date_dt": int(time.time())})

    return md_data

