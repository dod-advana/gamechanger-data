import psycopg2
from psycopg2.extras import RealDictCursor


def vendor_org_hierarchy(vendor_cage:str, dodacc_map: dict, data_conf_filter: dict) -> dict:
    vendor_org_hierarchy_extensions_metadata = {}
    dodacc_list = tuple(dodacc_map.keys())

    sql_vendor_org_hierarchy = data_conf_filter['eda']['sql_vendor_org_hierarchy_1']
    sql_cage_code_name = data_conf_filter['eda']['sql_vendor_org_hierarchy_2']
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

        if len(vendor_cage) != 0:
            cursor.execute(sql_cage_code_name, (vendor_cage,))
            cage_code_names = []
            rows = cursor.fetchall()
            for row in rows:
                items = {}
                col_names = [desc[0] for desc in cursor.description]
                for col in col_names:
                    val = row[col]
                    if val:
                        items[col + postfix_es] = val
                if len(items) > 0:
                    cage_code_names.append(items)
            vendor_org_hierarchy_extensions_metadata["cage_code" + postfix_es + "_n"] = cage_code_names

        if len(dodacc_list) != 0:
            cursor.execute(sql_vendor_org_hierarchy, (dodacc_list,))

            rows = cursor.fetchall()
            vendor_org_hierarchy_nodes = []
            for row in rows:
                items = {}
                col_names = [desc[0] for desc in cursor.description]
                for col in col_names:

                    if col == "dodaac_ric":
                        key_value = row[col]
                        val = dodacc_map.get(key_value)
                        items["dodaac_name" + postfix_es] = val
                        items["dodaac" + postfix_es] = key_value
                    else:
                        val = row[col]
                        if val:
                            items[col + postfix_es] = val
                vendor_org_hierarchy_nodes.append(items)

        vendor_org_hierarchy_extensions_metadata["vendor_org" + postfix_es + "_n"] = vendor_org_hierarchy_nodes

        # json_object = json.dumps(vendor_org_hierarchy_extensions_metadata, indent=4)
        # print(json_object)
        return vendor_org_hierarchy_extensions_metadata
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
    return vendor_org_hierarchy_extensions_metadata

