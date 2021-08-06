import psycopg2
import json
import psycopg2.extras
from dataPipelines.gc_eda_pipeline.utils.eda_utils import read_extension_conf


data_conf_filter = read_extension_conf()


def audit_file_exist(filename: str) -> bool:
    conn = psycopg2.connect(host=data_conf_filter['eda']['database']['hostname'],
                            port=data_conf_filter['eda']['database']['port'],
                            user=data_conf_filter['eda']['database']['user'],
                            password=data_conf_filter['eda']['database']['password'],
                            dbname=data_conf_filter['eda']['database']['db'],
                            cursor_factory=psycopg2.extras.DictCursor)
    sql_audit_file_exist = """SELECT filename FROM public.gc_file_process_status WHERE filename = %s; """
    with conn.cursor() as cursor:
        cursor.execute(sql_audit_file_exist, (filename,))
        if cursor.fetchone() is not None:
            return True
        else:
            return False


def audit_file_with_base_path_exist(filename: str, base_path: str) -> bool:
    conn = psycopg2.connect(host=data_conf_filter['eda']['database']['hostname'],
                            port=data_conf_filter['eda']['database']['port'],
                            user=data_conf_filter['eda']['database']['user'],
                            password=data_conf_filter['eda']['database']['password'],
                            dbname=data_conf_filter['eda']['database']['db'],
                            cursor_factory=psycopg2.extras.DictCursor)
    sql_audit_file_exist = """SELECT filename FROM public.gc_file_process_status 
        WHERE filename = %s AND base_path = %s; """

    with conn.cursor() as cursor:
        cursor.execute(sql_audit_file_exist, (filename, base_path,))
        if cursor.fetchone() is not None:
            return True
        else:
            return False


def audit_get_failed_record(filename: str, base_path: str):
    conn = psycopg2.connect(host=data_conf_filter['eda']['database']['hostname'],
                            port=data_conf_filter['eda']['database']['port'],
                            user=data_conf_filter['eda']['database']['user'],
                            password=data_conf_filter['eda']['database']['password'],
                            dbname=data_conf_filter['eda']['database']['db'],
                            cursor_factory=psycopg2.extras.DictCursor)
    sql_audit_failed_record = """SELECT * FROM public.gc_file_process_fail WHERE filename = %s AND base_path = %s"""
    with conn.cursor() as cursor:
        cursor.execute(sql_audit_failed_record, (filename, base_path, ))
        row = cursor.fetchone()
        if row is not None:
            return {
                "filename": row['filename'],
                "base_path": row['base_path'],
                "reason": row['reason']
            }
        else:
            return None


def audit_get_record(filename: str) -> dict or None:
    conn = psycopg2.connect(host=data_conf_filter['eda']['database']['hostname'],
                            port=data_conf_filter['eda']['database']['port'],
                            user=data_conf_filter['eda']['database']['user'],
                            password=data_conf_filter['eda']['database']['password'],
                            dbname=data_conf_filter['eda']['database']['db'],
                            cursor_factory=psycopg2.extras.DictCursor)
    sql_audit_record = """SELECT * FROM public.gc_file_process_status WHERE filename = %s"""
    with conn.cursor() as cursor:
        cursor.execute(sql_audit_record, (filename,))
        row = cursor.fetchone()
        if row is not None:
            return {
                "filename": row['filename'],
                "eda_path":  row['eda_path'],
                "gc_path": row['gc_path'],
                "json_path": row['json_path'],
                "is_ocr": row['is_ocr'],
                "base_path": row['base_path'],
                "metadata_type": row['metadata_type'],
                "is_metadata_suc": row['is_metadata_suc'],
                "is_supplementary_file_missing": row['is_supplementary_file_missing'],
                "modified_date_dt": row['modified_date_dt']
            }
        else:
            return None


def audit_failed_record(data: list) -> None:
    conn = psycopg2.connect(host=data_conf_filter['eda']['database']['hostname'],
                            port=data_conf_filter['eda']['database']['port'],
                            user=data_conf_filter['eda']['database']['user'],
                            password=data_conf_filter['eda']['database']['password'],
                            dbname=data_conf_filter['eda']['database']['db'],
                            cursor_factory=psycopg2.extras.DictCursor)
    sql_audit_failed_record = """INSERT INTO public.gc_file_process_fail 
    SELECT 
        *
    FROM json_populate_recordset(NULL::public.gc_file_process_fail, %s) on CONFLICT (filename, base_path) DO NOTHING;
    """
    with conn.cursor() as cursor:
        cursor.execute(sql_audit_failed_record, (json.dumps(data),))
        conn.commit()


def audit_success_record(data: list) -> None:
    conn = psycopg2.connect(host=data_conf_filter['eda']['database']['hostname'],
                            port=data_conf_filter['eda']['database']['port'],
                            user=data_conf_filter['eda']['database']['user'],
                            password=data_conf_filter['eda']['database']['password'],
                            dbname=data_conf_filter['eda']['database']['db'],
                            cursor_factory=psycopg2.extras.DictCursor)
    sql_audit_success = """
    INSERT INTO public.gc_file_process_status
    SELECT
        *
    FROM json_populate_recordset(NULL::public.gc_file_process_status, %s) ON CONFLICT (filename) DO 
    UPDATE SET 
        base_path = EXCLUDED.base_path, 
        eda_path = EXCLUDED.eda_path,
        gc_path = EXCLUDED.gc_path, 
        json_path = EXCLUDED.json_path, 
        metadata_type = EXCLUDED.metadata_type, 
        is_metadata_suc = EXCLUDED.is_metadata_suc, 
        is_ocr = EXCLUDED.is_ocr, 
        modified_date_dt = EXCLUDED.modified_date_dt, 
        is_supplementary_file_missing = EXCLUDED.is_supplementary_file_missing;
    """
    with conn.cursor() as cursor:
        cursor.execute(sql_audit_success, (json.dumps(data),))
        # print(cursor.query)
        conn.commit()
