

def format_supplementary_data(json_info, date_fields_l):
    if isinstance(json_info, dict):
        for key in list(json_info.keys()):
            result_date = json_info[key]
            if isinstance(json_info[key], list):
                append = "_eda_ext_n"
            elif isinstance(json_info[key], dict):
                append = "_eda_ext_n"
            else:
                key_lower = key.lower()
                val = json_info[key]
                if key_lower in date_fields_l and val is not None:
                    append = "_eda_ext_dt"
                    result_date = val
                else:
                    append = "_eda_ext"
                    result_date = val
                    if key_lower in date_fields_l and val is not None:
                        append = "_eda_ext_dt"
                        result_date = val
            key_lower = key.lower() + append
            json_info[key_lower] = result_date
            del json_info[key]
            format_supplementary_data(json_info[key_lower], date_fields_l)

    elif isinstance(json_info, list):
        for item in json_info:
            format_supplementary_data(item, date_fields_l)