from dataPipelines.gc_eda_pipeline.utils.eda_utils import read_extension_conf

import click
import psycopg2


@click.command()
@click.option(
    '-s',
    '--staging-folder',
    help="A temp folder for which the eda data will be staged for processing.",
    required=True,
    type=str,
)
def run(staging_folder: str):
    print("Cron Daily Process")

    sql_check_for_daily_process = data_conf_filter['eda']['sql_check_if_pds_metadata_exist']

    # Load Extensions configuration files.
    data_conf_filter = read_extension_conf()

    conn = psycopg2.connect(host=data_conf_filter['eda']['database']['hostname'],
                            port=data_conf_filter['eda']['database']['port'],
                            user=data_conf_filter['eda']['database']['user'],
                            password=data_conf_filter['eda']['database']['password'],
                            dbname=data_conf_filter['eda']['database']['db'],
                            cursor_factory=psycopg2.extras.DictCursor)
    cursor = conn.cursor()

    cursor.execute(sql_check_if_pds_metadata_exist, (filename,))











