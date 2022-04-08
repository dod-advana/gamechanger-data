from dataPipelines.gc_eda_pipeline.migration.connection import ConnectionPool


def vendor_org_hierarchy(vendor_cage: str, dodacc_map: dict, data_conf_filter: dict, db_pool: ConnectionPool) -> dict:
    vendor_org_hierarchy_extensions_metadata = {}
    dodacc_list = tuple(dodacc_map.keys())

    sql_vendor_org_hierarchy = data_conf_filter['eda']['sql_vendor_org_hierarchy_1']
    sql_cage_code_name = data_conf_filter['eda']['sql_vendor_org_hierarchy_2']
    postfix_es = data_conf_filter['eda']['postfix_es']

    # conn = None
    try:
        # conn = psycopg2.connect(host=data_conf_filter['eda']['database']['hostname'],
        #                         port=data_conf_filter['eda']['database']['port'],
        #                         user=data_conf_filter['eda']['database']['user'],
        #                         password=data_conf_filter['eda']['database']['password'],
        #                         dbname=data_conf_filter['eda']['database']['db'],
        #                         cursor_factory=psycopg2.extras.DictCursor)
        # cursor = conn.cursor()




        if len(vendor_cage) != 0:
            rows = db_pool.fetchall_sql(sql_cage_code_name, (vendor_cage,))
            cage_code_names = []

            items = {}
            for row in rows:
                data = dict(row)
                for col_name, val in data.items():
                    items[col_name + postfix_es] = str(val)

                if len(items) > 0:
                    cage_code_names.append(items)
            vendor_org_hierarchy_extensions_metadata["cage_code" + postfix_es + "_n"] = cage_code_names

        if len(dodacc_list) != 0:
            rows = db_pool.fetchall_sql(sql_vendor_org_hierarchy, (dodacc_list,))
            vendor_org_hierarchy_nodes = []

            items = {}
            for row in rows:
                data = dict(row)
                for col_name, val in data.items():
                    if col_name == "dodaac_ric":
                        items[col_name + postfix_es] = str(val)
                        key_value = val
                        val = dodacc_map.get(key_value)
                        items["dodaac_name" + postfix_es] = val
                        items["dodaac" + postfix_es] = key_value
                    else:
                        if val:
                            items[col_name + postfix_es] = val
                vendor_org_hierarchy_nodes.append(items)
        vendor_org_hierarchy_extensions_metadata["vendor_org" + postfix_es + "_n"] = vendor_org_hierarchy_nodes

        # json_object = json.dumps(vendor_org_hierarchy_extensions_metadata, indent=4)
        # print(json_object)
        return vendor_org_hierarchy_extensions_metadata
    except Exception as error:
        print(error)

    return vendor_org_hierarchy_extensions_metadata

