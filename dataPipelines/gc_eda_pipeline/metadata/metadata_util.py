

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

def title(filename: str) -> str:
    parsed = filename.split('-')

    if (len(parsed) - 1) == 9:
        contract = parsed[2]
        ordernum = parsed[3]
        acomod = parsed[4]
        pcomod = parsed[5]
        if pcomod == 'empty':
            modification = acomod
        else:
            modification = pcomod
    elif (len(parsed) - 1) == 10:
        contract = parsed[3]
        ordernum = parsed[4]
        acomod = parsed[5]
        pcomod = parsed[6]
        if pcomod == 'empty':
            modification = acomod
        else:
            modification = pcomod
    elif (len(parsed) - 1) == 11:
        contract = parsed[4]
        ordernum = parsed[5]
        acomod = parsed[6]
        pcomod = parsed[7]
        if pcomod == 'empty':
            modification = acomod
        else:
            modification = pcomod
    elif (len(parsed) - 1) == 12:
        contract = parsed[5]
        ordernum = parsed[6]
        acomod = parsed[7]
        pcomod = parsed[8]
        if pcomod == 'empty':
            modification = acomod
        else:
            modification = pcomod
    elif (len(parsed) - 1) == 13:
        contract = parsed[6]
        ordernum = parsed[7]
        acomod = parsed[8]
        pcomod = parsed[9]
        if pcomod == 'empty':
            modification = acomod
        else:
            modification = pcomod
    else:
        return "NA"

    return contract + "-" + ordernum + "-" + modification