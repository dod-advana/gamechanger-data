import psycopg2
import json
import psycopg2.extras
from dataPipelines.gc_ppbe_pipeline.utils.ppbe_utils import read_extension_conf
from dataPipelines.gc_ppbe_pipeline.utils.ppbe_job_type import PPBEJobType


data_conf_filter = read_extension_conf()


def insert_data_db(data: list, job_type: PPBEJobType):
    if job_type == PPBEJobType.RDTE:
        insert_data_rdte_db(data)
    elif job_type == PPBEJobType.PROCUREMENT:
        insert_data_procurement_db(data)


def insert_data_rdte_db(data: list) -> None:

    conn = psycopg2.connect(host=data_conf_filter['ppbe']['database']['hostname'],
                            port=data_conf_filter['ppbe']['database']['port'],
                            user=data_conf_filter['ppbe']['database']['user'],
                            password=data_conf_filter['ppbe']['database']['password'],
                            dbname=data_conf_filter['ppbe']['database']['db'],
                            cursor_factory=psycopg2.extras.DictCursor)
    sql_insert = """INSERT INTO ppbe.rdte 
    SELECT 
        *
    FROM json_populate_recordset(NULL::ppbe.rdte, %s);
    """

    with conn.cursor() as cursor:
        cursor.execute(sql_insert, (json.dumps(data),))
        conn.commit()


def insert_data_procurement_db(data: list) -> None:

    conn = psycopg2.connect(host=data_conf_filter['ppbe']['database']['hostname'],
                            port=data_conf_filter['ppbe']['database']['port'],
                            user=data_conf_filter['ppbe']['database']['user'],
                            password=data_conf_filter['ppbe']['database']['password'],
                            dbname=data_conf_filter['ppbe']['database']['db'],
                            cursor_factory=psycopg2.extras.DictCursor)
    sql_insert = """INSERT INTO ppbe.procurement 
    SELECT 
        *
    FROM json_populate_recordset(NULL::ppbe.procurement, %s);
    """

    with conn.cursor() as cursor:
        cursor.execute(sql_insert, (json.dumps(data),))
        conn.commit()

