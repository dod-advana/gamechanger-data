import click
import sys
import psycopg2
from psycopg2.extras import RealDictCursor

from dataPipelines.gc_eda_pipeline.utils.eda_utils import read_extension_conf
from dataPipelines.gc_eda_pipeline.gc_eda_ocr_pipeline import ingestion as ingestion_ocr
from dataPipelines.gc_eda_pipeline.gc_eda_metadata_pipline import ingestion as ingestion_metadata_es
from dataPipelines.gc_eda_pipeline.conf import Conf
from datetime import datetime

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

def run(staging_folder: str,  max_workers: int, workers_ocr: int,):
    print("Daily -- CronJob Process ---")

    # Load Extensions configuration files.
    data_conf_filter = read_extension_conf()

    sql_daily_process = data_conf_filter['eda']['sql_daily_process']
    sql_is_in_process_state = data_conf_filter['eda']['sql_is_in_process_state']
    sql_set_daily_status_on_log = data_conf_filter['eda']['sql_set_daily_status_on_log']
    sql_insert_process_status = data_conf_filter['eda']['sql_insert_process_status']
    aws_s3_daily_pdf_prefix = data_conf_filter['eda']['aws_s3_daily_pdf_prefix']

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
            cursor.execute(sql_daily_process)
            print("There is no dataset that need to be process")
            sys.exit("There is no dataset that need to be process")
        else:
            output_path = row['output_path']
            today_date = datetime.today().strftime('%Y/%m/%d') + "/"
            if today_date == output_path:
                print("Skip Today's date")
                sys.exit("There is no dataset that need to be process")

            audit_moved_loc = row['audit_moved_loc']
            process_directory = ''.join([aws_s3_daily_pdf_prefix, output_path])

            print(process_directory)
            if Conf.s3_utils.prefix_exists(prefix_path=process_directory):
                cursor.execute(sql_set_daily_status_on_log, ("Processing", audit_moved_loc, output_path))
                print(f"Processing {cursor.query}")
                conn.commit()

                ingestion_ocr(staging_folder=staging_folder, workers_ocr=workers_ocr, max_workers=max_workers,
                              aws_s3_input_pdf_prefix=process_directory, loop_number=50000)

                ingestion_metadata_es(max_workers=max_workers, aws_s3_input_pdf_prefix=process_directory)

                # Update Daily EDA Table
                cursor.execute(sql_set_daily_status_on_log, ("Completed", audit_moved_loc, output_path))
                print(f"Completed {cursor.query}")
                conn.commit()

                # Update
                cursor.execute(sql_insert_process_status, (process_directory, 'Completed'))
                print(f"GC -- Completed {cursor.query}")
                conn.commit()
            else:
                cursor.execute(sql_set_daily_status_on_log, ("Missing", audit_moved_loc, output_path))
                print(f"Missing {cursor.query}")
                conn.commit()
                print(f"The follow prefix was not found in S3 {process_directory}")
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()


if __name__ == '__main__':
    run()







