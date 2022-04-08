import sys
import threading

import psycopg2
import psycopg2.extras
import time
from psycopg2.pool import ThreadedConnectionPool, SimpleConnectionPool
from threading import Lock
from typing import Optional
import json
from threading import Semaphore




def audit_is_processed(db_pool: ThreadedConnectionPool, filename: str) -> (str, str):
    sql_audit_file_exist = """SELECT filename, base_path FROM public.gc_file_process_status WHERE filename = %s """
    conn = db_pool.getconn()

    conn = db_pool.getconn()
    cursor = conn.cursor()
    cursor.execute(sql_audit_file_exist, (filename,))
    data = cursor.fetchone()
    db_pool.putconn(conn)
    if data is not None:
        result = dict(data)
        return result['filename'], result['base_path']
    else:
        return None, None

# def audit_file_with_base_path_exist(self, filename: str, base_path: str) -> bool:
#     sql_audit_failed_record = """SELECT * FROM public.gc_file_process_fail WHERE filename = %s AND base_path = %s"""
#     data = self.fetchone_sql(sql_audit_failed_record, (filename, base_path,))
#     if data:
#         return True
#     else:
#         return False

# def audit_get_failed_record(self, filename: str, base_path: str):
#     sql_audit_failed_record = """SELECT * FROM public.gc_file_process_fail WHERE filename = %s AND base_path = %s"""
#     result = self.fetchone_sql(sql_audit_failed_record, (filename, base_path,))
#     if result is not None:
#         return {
#             "filename": result['filename'],
#             "base_path": result['base_path'],
#             "reason": result['reason']
#         }
#     else:
#         return None

# def audit_get_record(self, filename: str) -> dict or None:
#     sql_audit_record = """SELECT * FROM public.gc_file_process_status WHERE filename = %s"""
#     row = self.fetchone_sql(sql_audit_record, (filename,))
#     if row is not None:
#         return {
#             "filename": row['filename'],
#             "eda_path": row['eda_path'],
#             "gc_path": row['gc_path'],
#             "json_path": row['json_path'],
#             "is_ocr": row['is_ocr'],
#             "base_path": row['base_path'],
#             "metadata_type": row['metadata_type'],
#             "is_metadata_suc": row['is_metadata_suc'],
#             "is_supplementary_file_missing": row['is_supplementary_file_missing'],
#             "modified_date_dt": row['modified_date_dt']
#         }
#     else:
#         return None

def audit_failed_record(db_pool: ThreadedConnectionPool, data: list) -> None:
    sql_audit_failed_record = """INSERT INTO public.gc_file_process_fail
      SELECT
          *
      FROM json_populate_recordset(NULL::public.gc_file_process_fail, %s) on CONFLICT (filename, base_path) DO NOTHING;
      """
    conn = db_pool.getconn()
    cursor = conn.cursor()
    cursor.execute(sql_audit_failed_record, (json.dumps(data),))
    conn.commit()
    db_pool.putconn(conn)


def audit_success_record(db_pool: ThreadedConnectionPool, data: list) -> None:
    sql_audit_success = """
    INSERT INTO public.gc_file_process_status
    SELECT
        *
    FROM json_populate_recordset(NULL::public.gc_file_process_status, %s) ON CONFLICT (filename) DO
    UPDATE SET
        is_ocr = EXCLUDED.is_ocr,
        is_pds = EXCLUDED.is_pds,
        is_syn = EXCLUDED.is_syn,
        is_fpds_ng = EXCLUDED.is_fpds_ng,
        is_elasticsearch = EXCLUDED.is_elasticsearch,
        is_supplementary_file_missing = EXCLUDED.is_supplementary_file_missing,
        modified_date_dt = EXCLUDED.modified_date_dt;
    """

    conn = db_pool.getconn()
    cursor = conn.cursor()
    cursor.execute(sql_audit_success, (json.dumps(data),))
    conn.commit()
    db_pool.putconn(conn)


def audit_fetch_all_records_for_base_path(db_pool: ThreadedConnectionPool, base_path: str):
    data = {}
    conn = db_pool.getconn()
    cursor = conn.cursor()
    sql = """SELECT filename, eda_path, base_path, gc_path, json_path, is_ocr,  is_pds, is_syn,  is_fpds_ng,
        is_elasticsearch,  is_supplementary_file_missing
        FROM public.gc_file_process_status WHERE base_path = %s;"""
    cursor.execute(sql, (base_path,))
    rows = cursor.fetchall()
    for row in rows:
        data_row = dict(row)
        data[row['filename']] = data_row
    db_pool.putconn(conn)
    return data


