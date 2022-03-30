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


class WaitingConnectionPool:
    def __init__(self, minconn: int, maxconn: int, *args, **kwargs):
        self.minconn = minconn
        self.maxconn = maxconn
        self.args = args
        self.kwargs = kwargs
        self._pool: Optional[ThreadedConnectionPool] = None
        self._lock = Lock()
        self._poolSemaphore = threading.Semaphore(95)

    def _get_pool(self) -> ThreadedConnectionPool:
        with self._lock:
            while self._pool is None or self._pool.closed:
                try:
                    self._pool = ThreadedConnectionPool(self.minconn, self.maxconn, *self.args, **self.kwargs)
                except psycopg2.OperationalError as e:
                    if e.pgerror is not None:
                        # not a connection error. Only want to retry if server is currently
                        # unavailable, not if e.g. password is wrong
                        raise

                    print('Connection to database failed. Retrying in 3 seconds')
                    time.sleep(3)

            return self._pool

    def getconn(self):
        self._poolSemaphore.acquire(blocking=True)
        # print("Pool is delivering connection")
        return self._get_pool().getconn()

    def putconn(self, conn):
        if self._pool is not None and not self._pool.closed:
            self._pool.putconn(conn)
            self._poolSemaphore.release()
            # print("Pool took back a connection")


class ConnectionPool:
    cc_pool = None

    def __init__(self, db_hostname: str, db_port_number: str , db_user_name: str, db_password: str, db_dbname: str, minconn=1, maxconn=95, multithreading=True):
        if multithreading:
            self.cc_pool = WaitingConnectionPool(minconn, maxconn, host=db_hostname, port=db_port_number, database=db_dbname,
                                                  user=db_user_name, password=db_password, cursor_factory=psycopg2.extras.DictCursor)
        else:
            self.cc_pool = SimpleConnectionPool(minconn, maxconn, host=db_hostname, port=db_port_number, database=db_dbname,
                                                  user=db_user_name, password=db_password, cursor_factory=psycopg2.extras.DictCursor)

    def exe_conn(self, sql, parms):
        conn = self.cc_pool.getconn()
        cursor = conn.cursor()
        cursor.execute(sql, parms)
        # cursor.mogrify(query)
        conn.commit()
        self.cc_pool.putconn(conn)
        return cursor

    def fetchone_sql(self, sql, parms):
        cursor = self.exe_conn(sql, parms)
        # desc = cursor.description
        fetchone = cursor.fetchone()
        # print(cursor.query)
        cursor.close()
        return fetchone

    def fetchall_sql(self, sql, parms):
        cursor = self.exe_conn(sql, parms)
        fetchall = cursor.fetchall()
        cursor.close()
        return fetchall

    def fetchmany_sql(self, sql, parms, size=1):
        cursor = self.exe_conn(sql, parms)
        fetchall = cursor.fetchmany(size)
        cursor.close()
        return fetchall

    def exe_sql(self, sql, parms):
        cursor = self.exe_conn(sql, parms)
        cursor.close()

    def close_all(self):
        self.cc_pool.closeall()

    def audit_is_processed(self, filename: str) -> (str, str):
        sql_audit_file_exist = """SELECT filename, base_path FROM public.gc_file_process_status WHERE filename = %s """
        data = self.fetchone_sql(sql_audit_file_exist, (filename,))
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

    def audit_failed_record(self, data: list) -> None:
        sql_audit_failed_record = """INSERT INTO public.gc_file_process_fail
        SELECT
            *
        FROM json_populate_recordset(NULL::public.gc_file_process_fail, %s) on CONFLICT (filename, base_path) DO NOTHING;
        """
        self.exe_sql(sql_audit_failed_record, (json.dumps(data),))

    def audit_success_record(self, data: list) -> None:
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
        self.exe_sql(sql_audit_success, (json.dumps(data), ))

    def audit_fetch_all_records_for_base_path(self, base_path: str):
        data = {}
        sql = """SELECT filename, eda_path, base_path, gc_path, json_path, is_ocr,  is_pds, is_syn,  is_fpds_ng,
            is_elasticsearch,  is_supplementary_file_missing
            FROM public.gc_file_process_status WHERE base_path = %s;"""
        rows = self.fetchall_sql(sql, (base_path,))
        for row in rows:
            data_row = dict(row)
            data[row['filename']] = data_row
        return data


# if __name__ == '__main__':
#     gp_pool = ConnectionPool(db_hostname="localhost", db_port_number="5432", db_user_name="postgres", db_password="password", db_dbname="eda", multithreading=True)
#     # gp_pool = ConnectionPool('localhost', 5432, 'eda', 'postgres', 'password', multithreading=True)
#     result = gp_pool.audit_file_exist(filename="EDAPDF-070D5AFC32802814E05400215A9BA3B8-SP070003D1380-0547-empty-05-PDS-2014-11-04.pdf",
#                                       base_path="eda/piee/unarchive_pdf/small_test_2")
#
#     audit_rec = {"filename": "aaaa", "eda_path": "aaaa", "base_path": "aaaa", "gc_path": "aaaa",
#                  "json_path": "aaaa", "is_ocr": None, "is_pds": False, "is_syn": False, "is_fpds_ng": False,
#                  "is_elasticsearch": False, "is_supplementary_file_missing": False,
#                  "modified_date_dt": int(time.time())}
#     audit_list = [audit_rec]
#
#     gp_pool.audit_success_record(audit_list)
