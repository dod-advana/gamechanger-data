import psycopg2
from psycopg2.extras import RealDictCursor


def line_item_details(data_conf_filter: dict, header_details_id: str) -> []:
    if header_details_id is None:
        return None

    sql_line_item_details = data_conf_filter['eda']['sql_line_item_details']
    postfix_es = data_conf_filter['eda']['postfix_es']

    conn = None
    try:
        conn = psycopg2.connect(host=data_conf_filter['eda']['database']['hostname'],
                                port=data_conf_filter['eda']['database']['port'],
                                user=data_conf_filter['eda']['database']['user'],
                                password=data_conf_filter['eda']['database']['password'],
                                dbname=data_conf_filter['eda']['database']['db'],
                                cursor_factory=psycopg2.extras.DictCursor)
        cursor = conn.cursor()
        cursor.execute(sql_line_item_details, (header_details_id,))
        rows = cursor.fetchall()
        line_details_nodes = []
        for row in rows:
            items = {}
            col_names = [desc[0] for desc in cursor.description]
            for col in col_names:
                val = row[col]
                if val:
                    items[col + postfix_es] = val
            line_details_nodes.append(items)
        return line_details_nodes
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
    return None
