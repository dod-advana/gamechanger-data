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
    print("Daily -- CronJob Process")

    # Load Extensions configuration files.
    data_conf_filter = read_extension_conf()

    # Check to see if there is already a currently processing data

    sql_daily_process = data_conf_filter['eda']['sql_daily_process']
    sql_is_in_process_state = data_conf_filter['eda']['sql_is_in_process_state']
    sql_set_status_to_processing = data_conf_filter['eda']['sql_set_status_to_processing']
    sql_set_status_to_completed = data_conf_filter['eda']['sql_set_status_to_completed']

    conn = None
    try:
        conn = psycopg2.connect(host=data_conf_filter['eda']['database']['hostname'],
                                port=data_conf_filter['eda']['database']['port'],
                                user=data_conf_filter['eda']['database']['user'],
                                password=data_conf_filter['eda']['database']['password'],
                                dbname=data_conf_filter['eda']['database']['db'],
                                cursor_factory=psycopg2.extras.DictCursor)
        cursor = conn.cursor()
        cursor.execute(sql_is_in_process_state)
        row = cursor.fetchone()
        if row is not None and row[0] == 'Processing':
            print("Currently there is already a dataset in process")
            sys.exit("Currently there is already dataset in process")

        cursor.execute(sql_daily_process)
        row = cursor.fetchone()
        if row is None:
            print("There is no dataset that need to be process")
            sys.exit("There is no dataset that need to be process")
        else:
            output_path = row['output_path']
            audit_moved_loc = row['audit_moved_loc']
            process_directory = ''.join([audit_moved_loc, output_path])

        if process_directory:
            cursor.execute(sql_set_status_to_processing, (audit_moved_loc, output_path))
            conn.commit()

            print(process_directory)
            ingestion(staging_folder=staging_folder, aws_s3_input_pdf_prefix=process_directory, max_workers=max_workers,
                      eda_job_type=eda_job_type, workers_ocr=workers_ocr, loop_number=50000)

            cursor.execute(sql_set_status_to_completed, (audit_moved_loc, output_path))
            conn.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()


if __name__ == '__main__':
    run()







