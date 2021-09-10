import psycopg2
import json
import psycopg2.extras
from dataPipelines.gc_ppbe_pipeline.utils.ppbe_utils import read_extension_conf


data_conf_filter = read_extension_conf()


def insert_data_rdte_into_db(data: list) -> None:

    conn = psycopg2.connect(host=data_conf_filter['ppbe']['database']['hostname'],
                            port=data_conf_filter['ppbe']['database']['port'],
                            user=data_conf_filter['ppbe']['database']['user'],
                            password=data_conf_filter['ppbe']['database']['password'],
                            dbname=data_conf_filter['ppbe']['database']['db'],
                            cursor_factory=psycopg2.extras.DictCursor)
    sql_insert = """INSERT INTO public.rdte 
    SELECT 
        *
    FROM json_populate_recordset(NULL::public.rdte, %s);
    """

    with conn.cursor() as cursor:
        cursor.execute(sql_insert, (json.dumps(data),))
        conn.commit()

