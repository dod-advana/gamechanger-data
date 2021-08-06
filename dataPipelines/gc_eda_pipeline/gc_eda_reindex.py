import click
import sys
import psycopg2
from psycopg2.extras import RealDictCursor

from dataPipelines.gc_eda_pipeline.utils.eda_utils import read_extension_conf
from dataPipelines.gc_eda_pipeline.gc_eda_pipeline import ingestion
from dataPipelines.gc_eda_pipeline.utils.eda_job_type import EDAJobType


@click.command()
@click.option(
    '-s',
    '--staging-folder',
    help="A temp folder for which the eda data will be staged for processing.",
    required=True,
    type=str,
)
@click.option(
    '-p',
    '--workers-ocr',
    required=False,
    default=-1,
    type=int,
    help="Multiprocessing. If treated like flag, will do max cores available. \
                if treated like option will take integer for number of cores.",
)
@click.option(
    '--max-workers',
    required=False,
    default=-1,
    type=int,
    help="Multiprocessing. If treated like flag, will do max cores available. \
                if treated like option will take integer for number of cores.",
)
@click.option(
    '--eda-job-type',
    type=click.Choice([e.value for e in EDAJobType]),
    help="""Determines how the data should be processed, """,
    default=EDAJobType.NORMAL.value
)
def run(staging_folder: str,  max_workers: int, workers_ocr: int, eda_job_type: str):
    print("------ Re-Index Data ------")

    # Load Extensions configuration files.
    data_conf_filter = read_extension_conf()

    sql_reprocess_status = data_conf_filter['eda']['sql_reprocess_status']
    sql_reprocess_set_status_process = data_conf_filter['eda']['sql_reprocess_set_status_process']
    continue_to_process_data = True
    while continue_to_process_data:
        conn = None
        try:
            conn = psycopg2.connect(host=data_conf_filter['eda']['database']['hostname'],
                                    port=data_conf_filter['eda']['database']['port'],
                                    user=data_conf_filter['eda']['database']['user'],
                                    password=data_conf_filter['eda']['database']['password'],
                                    dbname=data_conf_filter['eda']['database']['db'],
                                    cursor_factory=psycopg2.extras.DictCursor)
            cursor = conn.cursor()
            cursor.execute(sql_reprocess_status)
            row = cursor.fetchone()

            if row is None:
                continue_to_process_data = False
                print("There is no dataset that need to be reprocess")
                sys.exit("There is no dataset that need to be reprocess")

            process_directory = row['s3_prefix']
            status = 'Processing'
            cursor.execute(sql_reprocess_set_status_process, (status, process_directory,))
            conn.commit()
            print(process_directory)

            ingestion(staging_folder=staging_folder, aws_s3_input_pdf_prefix=process_directory, max_workers=max_workers,
                      eda_job_type=eda_job_type, workers_ocr=workers_ocr, loop_number=50000)

            status = 'Completed'
            cursor.execute(sql_reprocess_set_status_process,  (status, process_directory,))
            conn.commit()
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
        finally:
            if conn is not None:
                conn.close()


if __name__ == '__main__':
    run()
