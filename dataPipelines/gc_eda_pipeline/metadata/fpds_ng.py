from dataPipelines.gc_eda_pipeline.metadata.metadata_util import extract_fpds_ng_quey_values
import psycopg2
from psycopg2.extras import RealDictCursor
from dataPipelines.gc_eda_pipeline.utils.eda_utils import read_extension_conf
from psycopg2.pool import ThreadedConnectionPool

data_conf_filter = read_extension_conf()


def __sql_fpds_ng_piid_less_or_equal_4_chars(idv_piid, piid, modification_number: list, db_pool_pbis: ThreadedConnectionPool, filename: str):
    sql_fpds_ng_piid_less_or_equal_4_chars = data_conf_filter['eda']['sql_fpds_ng_piid_less_or_equal_4_chars']
    postfix_es = data_conf_filter['eda']['postfix_es']

    # conn = None
    try:
        conn = db_pool_pbis.getconn()
        cursor = conn.cursor()
        cursor.execute(sql_fpds_ng_piid_less_or_equal_4_chars, (idv_piid, piid, tuple(modification_number),))
        # print("-------")
        # print(filename)
        # print("-------")
        # print(cursor.query)
        rows = cursor.fetchall()
        db_pool_pbis.putconn(conn)



        # conn = psycopg2.connect(host=data_conf_filter['eda']['database_pbis']['hostname'],
        #                         port=data_conf_filter['eda']['database_pbis']['port'],
        #                         user=data_conf_filter['eda']['database_pbis']['user'],
        #                         password=data_conf_filter['eda']['database_pbis']['password'],
        #                         dbname=data_conf_filter['eda']['database_pbis']['db'],
        #                         cursor_factory=psycopg2.extras.DictCursor)
        # cursor = conn.cursor()
        # # print(f"sql_fpds_ng_piid_more_than_4_chars :: {idv_piid} --  {piid}  --  {modification_number} ")
        # cursor.execute(sql_fpds_ng_piid_less_or_equal_4_chars, (idv_piid, piid, tuple(modification_number),))
        # # print(cursor.query)
        # rows = cursor.fetchall()
        date_filter = ['date_signed', 'closed_date', 'effective_date']
        # data = []
        items = {}
        for row in rows:
            # items = {}
            col_names = [desc[0] for desc in cursor.description]
            for col in col_names:
                val = row[col]
                if val:
                    if col.strip() in date_filter:
                        items[col + postfix_es + '_dt'] = __strip_end(str(val))
                    elif col.strip() == 'dollars_obligated':
                        items[col + postfix_es + '_f'] = float(val)
                    else:
                        items[col + postfix_es] = str(val)
            # data.append(items)
        return items
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    return None


def __sql_fpds_ng_piid_more_than_4_chars(piid: str, modification_number: list, db_pool_pbis: ThreadedConnectionPool, filename:str):
    sql_fpds_ng_piid_more_than_4_chars = data_conf_filter['eda']['sql_fpds_ng_piid_more_than_4_chars']
    postfix_es = data_conf_filter['eda']['postfix_es']

    # conn = None
    try:
        conn = db_pool_pbis.getconn()
        cursor = conn.cursor()
        cursor.execute(sql_fpds_ng_piid_more_than_4_chars, (piid, piid, tuple(modification_number),))
        # print("-------")
        # print(filename)
        # print(cursor.query)
        # print("-------")
        rows = cursor.fetchall()
        db_pool_pbis.putconn(conn)

        # conn = psycopg2.connect(host=data_conf_filter['eda']['database_pbis']['hostname'],
        #                         port=data_conf_filter['eda']['database_pbis']['port'],
        #                         user=data_conf_filter['eda']['database_pbis']['user'],
        #                         password=data_conf_filter['eda']['database_pbis']['password'],
        #                         dbname=data_conf_filter['eda']['database_pbis']['db'],
        #                         cursor_factory=psycopg2.extras.DictCursor)
        # cursor = conn.cursor()
        # print(f"sql_fpds_ng_piid_more_than_4_chars :: {piid}  --  {modification_number} ")
        # cursor.execute(sql_fpds_ng_piid_more_than_4_chars, (piid, tuple(modification_number),))
        # # print(cursor.query)
        # rows = cursor.fetchall()
        date_filter = ['date_signed', 'closed_date', 'effective_date']
        items = {}
        for row in rows:
            col_names = [desc[0] for desc in cursor.description]
            for col in col_names:
                val = row[col]
                if val:
                    if col.strip() in date_filter:
                        items[col + postfix_es + '_dt'] = __strip_end(str(val))
                    elif col.strip() == 'dollars_obligated':
                        items[col + postfix_es + '_f'] = float(val)
                    else:
                        items[col + postfix_es] = str(val)
            # data.append(items)
        return items
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    return None


def __strip_end(text):
    if text:
        return text[:10]
    return text

def fpds_ng(filename: str, db_pool_pbis: ThreadedConnectionPool):
    # fpds_ng =
    (idv_piid, piid, modification_number) = extract_fpds_ng_quey_values(filename)
    q_idv_piid = idv_piid
    q_modification_number = []
    q_piid = piid

    # The mod number’s need to be ‘00’ instead of null (or `empty`) and when piid’s are null (or `empty`),
    # you need to make the idv_piid the piid before querying the FPDS db
    if modification_number == 'empty' or modification_number is None:
        q_modification_number.append('00')
        q_modification_number.append('0')
    else:
        q_modification_number.append(modification_number)

    if piid == 'empty' or piid is None:
        q_piid = idv_piid

    fpds_data = None
    if q_piid and len(q_piid) > 4:
        fpds_data = __sql_fpds_ng_piid_more_than_4_chars(q_piid, q_modification_number, db_pool_pbis, filename)
    if piid and len(piid) <= 4:
        fpds_data = __sql_fpds_ng_piid_less_or_equal_4_chars(q_idv_piid, q_piid, q_modification_number, db_pool_pbis, filename)

    return fpds_data


if __name__ == '__main__':


    print(__strip_end("2016-01-21 00:00:00.000"))


#     filenames = ["EDAPDF-00B49ADF6C0854B7E05400215A9BA3BA-N0018910DZ027-1008-empty-09-PDS-2014-08-15.pdf",
#         "EDAPDF-0ba1e026-58f4-4599-b0a9-06827f933e78-H9222215D0022-0003-empty-24-PDS-2020-04-22.pdf",
#         "EDAPDF-0CA73B35B30D038EE05400215A9BA3BA-HQ014710D0011-0006-empty-12-PDS-2015-01-14.pdf",
#         "EDAPDF-0CA2081E6C020E5CE05400215A9BA3BA-GS23F9755H-M6700414F4045-empty-P00001-PDS-2015-01-14.pdf"
#         ]
#
#     for filename in filenames:
#         (idv_piid, piid, modification_number) = extract_fpds_ng_quey_values(filename)
#         print('idv_piid: ' + idv_piid + ' piid: ' + piid + ' modification_number: ' + modification_number)
#
#         if len(piid) > 4:
#             print("Greater then 4")
#             print("""IF PIID is more than 4 characters, perform join with the PDF based on
#             the values in the FPDS-NG columns entitled PIID AND Modification Num,
#              and the file name values in positions 2, 3, and 4
#              (note, position 1 is an IDV number, but including that is not necessary to perform a join)""")
#             print("Filename: " + filename)
#             data = __sql_fpds_ng_piid_more_than_4_chars(piid, modification_number)
#             print(data)
#
#         if len(piid) <= 4:
#             print("Less then or equal to 4")
#             print("""If the PIID is 4 or fewer characters, perform join with the PDF based on the values
#             in the FPDS-NG columns entitled IDV PIID, PIID AND Modification Num, and the file name values
#             in positions 1, 2, 3, and 4""")
#             print("Filename: " + filename)
#             data = __sql_fpds_ng_piid_less_or_equal_4_chars(idv_piid, piid, modification_number)
#             print(data)
#
#         print("-------------------------------------------------------------------------------------------------------")
