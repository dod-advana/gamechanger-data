from dataPipelines.gc_eda_pipeline.database.connection import ConnectionPool


def line_item_details(data_conf_filter: dict, header_details_id: str, db_pool: ConnectionPool) -> []:
    if header_details_id is None:
        return None

    sql_line_item_details = data_conf_filter['eda']['sql_line_item_details']
    postfix_es = data_conf_filter['eda']['postfix_es']

    try:
        rows = db_pool.fetchall_sql(sql_line_item_details, (header_details_id,))
        line_details_nodes = []
        for row in rows:
            items = {}
            data = dict(row)
            for col_name, val in data.items():
                if val:
                    items[col_name + postfix_es] = str(val)
            line_details_nodes.append(items)
        return line_details_nodes
    except Exception as error:
        print(error)
    return None
