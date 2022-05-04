

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


def mod_identifier(filename: str) -> str:
    acomod = None
    pcomod = None
    parsed = filename.split('-')
    if (len(parsed) - 1) == 9:
        contract = parsed[2]
        ordernum = parsed[3]
        acomod = parsed[4]
        pcomod = parsed[5]
    elif (len(parsed) - 1) == 10:
        contract = parsed[3]
        ordernum = parsed[4]
        acomod = parsed[5]
        pcomod = parsed[6]
    elif (len(parsed) - 1) == 11:
        contract = parsed[4]
        ordernum = parsed[5]
        acomod = parsed[6]
        pcomod = parsed[7]
    elif (len(parsed) - 1) == 12:
        contract = parsed[5]
        ordernum = parsed[6]
        acomod = parsed[7]
        pcomod = parsed[8]
    elif (len(parsed) - 1) == 13:
        contract = parsed[6]
        ordernum = parsed[7]
        acomod = parsed[8]
        pcomod = parsed[9]

    if acomod == "empty" and pcomod == "empty":
        return "base_award"
    else:
        return ""


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


def extract_fpds_ng_quey_values(filename: str) -> (str, str, str):
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
        return None, None, None

    # idv_piid <-- contract
    # piid <-- ordernum
    # modification_number <--modification
    idv_piid = contract
    piid = ordernum
    modification_number = modification
    return idv_piid, piid, modification_number


def vu(idv_piid: str, piid: str, modification_number: str):
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


    print(f"final q_idv_piid: {q_idv_piid}, q_piid: {q_piid}, q_modification_number: {str(q_modification_number)}")


    if q_piid and len(q_piid) > 4:
        print(f"We would use q_piid: {q_piid}, q_modification_number : {str(q_modification_number)}")
    if piid and len(piid) <= 4:
        print(f"We would use q_idv_piid: {q_idv_piid}, q_piid: {q_piid}, q_modification_number : {str(q_modification_number)}")

    # fpds_data = None
    # if q_piid and len(q_piid) > 4:
    #     fpds_data = __sql_fpds_ng_piid_more_than_4_chars(q_piid, q_modification_number)
    # if piid and len(piid) <= 4:
    #     fpds_data = __sql_fpds_ng_piid_less_or_equal_4_chars(q_idv_piid, q_piid, q_modification_number)

    # return fpds_data

if __name__ == "__main__":
    # https: // search.advana.data.mil /  # /pdfviewer/gamechanger?filename=gamechanger/projects/eda/pdf/piee/daily_piee_untarred/edapdf/2021/03/17/EDAPDF-bbd01293-076d-433a-a518-5c6522fe795b-HQ003421C0005-empty-empty-empty-PDS-2021-03-16.pdf&prevSearchText=undefined&pageNumber=0&cloneIndex=eda
    # https: // search.advana.data.mil /  # /pdfviewer/gamechanger?filename=gamechanger/projects/eda/pdf/piee/unarchive_pdf/daily/20210308/pdf_dly_39/EDAPDF-3c758ac4-4748-4f1b-8a66-8f17ee563d67-N6833521C0077-empty-empty-empty-PDS-2020-10-06.pdf&prevSearchText=undefined&pageNumber=0&cloneIndex=eda
    test = "EDAPDF-12f0f703-fb72-4abf-99ad-52fa5957bda4-GS00T07NSD0038-HC101320FD730-empty-P00001-PDS-2020-11-25.pdf"
    (idv_piid, piid, modification_number) = extract_fpds_ng_quey_values(test)

    print(f"idv_piid: {idv_piid}, piid: {piid} modification_number: {modification_number}" )
    vu(idv_piid, piid, modification_number)
