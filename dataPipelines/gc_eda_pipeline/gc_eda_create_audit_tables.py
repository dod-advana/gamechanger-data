import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import pool
from dataPipelines.gc_eda_pipeline.utils.eda_utils import read_extension_conf


def run():
    data_conf_filter = read_extension_conf()

    try:
        conn_pool = psycopg2.pool.SimpleConnectionPool(minconn=1, maxconn=30, host=data_conf_filter['eda']['database']['hostname'],
                                                       port=data_conf_filter['eda']['database']['port'],
                                                       user=data_conf_filter['eda']['database']['user'],
                                                       password=data_conf_filter['eda']['database']['password'],
                                                       dbname=data_conf_filter['eda']['database']['db'],
                                                       cursor_factory=psycopg2.extras.DictCursor,)

        if conn_pool:
            print("Connection pool created successfully")
    except (Exception, psycopg2.DatabaseError) as error:
        print("Error while connecting to PostgreSQL", error)


    sql_create_gc_file_process_fail = """
        CREATE TABLE IF NOT EXISTS public.gc_file_process_fail
        (
            filename text COLLATE pg_catalog."default" NOT NULL,
            reason text COLLATE pg_catalog."default",
            base_path text COLLATE pg_catalog."default" NOT NULL,
            modified_date_dt bigint,
            CONSTRAINT gc_file_process_fail_pkey PRIMARY KEY (filename, base_path)
        )"""
    sql_create_gc_file_process_fail_index_base_path = """
        CREATE INDEX IF NOT EXISTS gc_file_process_fail_base_path_index
            ON public.gc_file_process_fail USING btree
            (base_path COLLATE pg_catalog."default" ASC NULLS LAST)
            TABLESPACE pg_default;
        """

    sql_create_gc_file_process_fail_index_filename = """
        CREATE INDEX IF NOT EXISTS gc_file_process_fail_filename_index
            ON public.gc_file_process_fail USING btree
            (filename COLLATE pg_catalog."default" ASC NULLS LAST)
            TABLESPACE pg_default;
    """

    sql_gc_file_process_status = """
    CREATE TABLE IF NOT EXISTS public.gc_file_process_status
    (
        filename text COLLATE pg_catalog."default" NOT NULL,
        eda_path text COLLATE pg_catalog."default",
        base_path text COLLATE pg_catalog."default",
        gc_path text COLLATE pg_catalog."default",
        json_path text COLLATE pg_catalog."default",
        is_ocr boolean,
        is_pds boolean,
        is_syn boolean,
        is_fpds_ng boolean,
        is_elasticsearch boolean,
        is_supplementary_file_missing boolean,
        modified_date_dt bigint,
        CONSTRAINT gc_file_process_status_pkey PRIMARY KEY (filename)
    )"""

    sql_gc_file_process_status_index_base_path = """    
    CREATE INDEX IF NOT EXISTS eda_basepath_index
        ON public.gc_file_process_status USING btree
        (base_path COLLATE pg_catalog."default" ASC NULLS LAST)
        TABLESPACE pg_default;
    """
    sql_gc_file_process_status_index_filename = """
    CREATE INDEX IF NOT EXISTS gc_file_process_status_filename_index
        ON public.gc_file_process_status USING btree
        (filename COLLATE pg_catalog."default" ASC NULLS LAST)
        TABLESPACE pg_default;"""



    try:
        conn = conn_pool.getconn()
        with conn.cursor() as cursor:
            cursor.execute(sql_create_gc_file_process_fail)
            conn.commit()
            cursor.execute(sql_create_gc_file_process_fail_index_base_path)
            conn.commit()
            cursor.execute(sql_create_gc_file_process_fail_index_filename)
            conn.commit()
            cursor.execute(sql_gc_file_process_status)
            conn.commit()
            cursor.execute(sql_gc_file_process_status_index_base_path)
            conn.commit()
            cursor.execute(sql_gc_file_process_status_index_filename)
            conn.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        conn_pool.putconn(conn)

    print("Done")


if __name__ == '__main__':
    run()
