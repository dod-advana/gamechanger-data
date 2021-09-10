from dataPipelines.gc_ppbe_pipeline.process_file_type.job_type_rdte import process_rdte
from dataPipelines.gc_ppbe_pipeline.process_file_type.job_type_procurement import process_procurement
from dataPipelines.gc_ppbe_pipeline.utils.ppbe_job_type import PPBEJobType


def transform(data: dict, job_type: PPBEJobType):
    if job_type == PPBEJobType.RDTE:
        process_rdte(data)
    elif job_type == PPBEJobType.PROCUREMENT:
        process_procurement(data)

