from dataPipelines.gc_eda_pipeline.metadata.metadata_util import format_supplementary_data


def extract_pds(data_conf_filter: dict, data: dict, extensions_metadata: dict):
    date_fields_l = data_conf_filter['eda']['sql_filter_fields']['date']
    extracted_data_eda_n = {}
    format_supplementary_data(data, date_fields_l)

    modification_number = populate_modification(data)
    if modification_number:
        extracted_data_eda_n["modification_number_eda_ext"] = modification_number

    award_id, referenced_idv = populate_award_id_referenced_idv(data, extensions_metadata)
    if award_id:
        extracted_data_eda_n["award_id_eda_ext"] = award_id
    if referenced_idv:
        extracted_data_eda_n["referenced_idv_eda_ext"] = referenced_idv

    contract_admin_office_dodaac, contract_admin_agency_name, contract_payment_office_dodaac, contract_payment_office_name = populate_address(data)
    if contract_admin_office_dodaac:
        extracted_data_eda_n["contract_admin_office_dodaac_eda_ext"] = contract_admin_office_dodaac
    if contract_admin_agency_name:
        extracted_data_eda_n["contract_admin_agency_name_eda_ext"] = contract_admin_agency_name
    if contract_payment_office_dodaac:
        extracted_data_eda_n["contract_payment_office_dodaac_eda_ext"] = contract_payment_office_dodaac
    if contract_payment_office_name:
        extracted_data_eda_n["contract_payment_office_name_eda_ext"] = contract_payment_office_name

    vendor_name, vendor_duns, vendor_cage = populate_vendor(data)
    if vendor_name:
        extracted_data_eda_n["vendor_name_eda_ext"] = vendor_name
    if vendor_duns:
        extracted_data_eda_n["vendor_duns_eda_ext"] = vendor_duns
    if vendor_cage:
        extracted_data_eda_n["vendor_cage_eda_ext"] = vendor_cage

    contract_issue_office_name, contract_issue_office_dodaac, dodaac_org_type = populate_contract_issue_office_name_and_contract_issue_office_dodaa(data)
    if contract_issue_office_name:
        extracted_data_eda_n["contract_issue_office_name_eda_ext"] = contract_issue_office_name
    if contract_issue_office_dodaac:
        extracted_data_eda_n["contract_issue_office_dodaac_eda_ext"] = contract_issue_office_dodaac
    if dodaac_org_type:
        extracted_data_eda_n["dodaac_org_type_eda_ext"] = dodaac_org_type

    sub_vendor_name, sub_vendor_duns, sub_vendor_cage = populate_vendor_sub(data)
    if sub_vendor_name:
        extracted_data_eda_n["sub_vendor_name_eda_ext"] = sub_vendor_name
    if sub_vendor_duns:
        extracted_data_eda_n["sub_vendor_duns_eda_ext"] = sub_vendor_duns
    if sub_vendor_cage:
        extracted_data_eda_n["sub_vendor_cage_eda_ext"] = sub_vendor_cage

    effective_date, signature_date = contract_effective_and_signed_date(data)
    if effective_date:
        extracted_data_eda_n["effective_date_eda_ext_dt"] = effective_date
    if signature_date:
        extracted_data_eda_n["signature_date_eda_ext_dt"] = signature_date

    total_obligated_amount = populate_total_obligated_amount(data)
    if total_obligated_amount:
        extracted_data_eda_n["total_obligated_amount_eda_ext_f"] = total_obligated_amount

    naics = populate_naics(data)
    if naics:
        extracted_data_eda_n["naics_eda_ext"] = naics

    return {"extracted_data_eda_n": extracted_data_eda_n}


# To populate Modifications
def populate_modification(data: dict) -> str:
    if "metadata_eda_ext_n" in data:
        metadata = data.get("metadata_eda_ext_n")
        modification_number = metadata.get("modification_eda_ext")
        if modification_number:
            return modification_number
        else:
            return "Award"


# To populate Award ID, ReferencedIDV
def populate_award_id_referenced_idv(data: dict, extensions_metadata: dict) -> (str, str):
    order_number = None
    contract_number = None
    award_id = None
    referenced_idv = None
    if "metadata_eda_ext_n" in data:
        metadata = data.get("metadata_eda_ext_n")
        if metadata.get("deliveryorder_eda_ext"):
            order_number = metadata.get("deliveryorder_eda_ext")
        if metadata.get("contract_eda_ext"):
            contract_number = metadata.get("contract_eda_ext")
        if order_number and contract_number:
            referenced_idv = extensions_metadata.get("pds_contract_eda_ext")
            award_id = extensions_metadata.get("pds_ordernum_eda_ext")
        elif order_number and contract_number:
            award_id = extensions_metadata.get("pds_ordernum_eda_ext")
        elif order_number and contract_number:
            award_id = extensions_metadata.get("pds_contract_eda_ext")
    return award_id, referenced_idv


# To populate address fields
def populate_address(data) -> (str, str, str, str):
    contract_admin_office_row_id = None
    paying_office_row_id = None
    contract_admin_agency_name = None
    contract_admin_office_dodaac = None
    contract_payment_office_name = None
    contract_payment_office_dodaac = None
    if "address_details_eda_ext_n" in data:
        for address_detail in data["address_details_eda_ext_n"]:
            if address_detail.get("address_desc_eda_ext") == "Contract Administrative Office":
                contract_admin_office_row_id = address_detail.get("row_id_eda_ext")
            if address_detail.get("address_desc_eda_ext") == "Paying Office":
                paying_office_row_id = address_detail.get("row_id_eda_ext")

    if "address_eda_ext_n" in data:
        for address in data["address_eda_ext_n"]:
            if address.get("fk_address_details_eda_ext") == contract_admin_office_row_id:
                contract_admin_agency_name = address.get("org_name_eda_ext")
                contract_admin_office_dodaac = address.get("orgid_dodaac_eda_ext")

            if address.get("fk_address_details_eda_ext") == paying_office_row_id:
                contract_payment_office_name = address.get("org_name_eda_ext")
                contract_payment_office_dodaac = address.get("orgid_dodaac_eda_ext")

    return contract_admin_agency_name, contract_admin_office_dodaac, contract_payment_office_name, contract_payment_office_dodaac


# To populate Vendor
def populate_vendor(data: dict) -> (str, str, str):
    row_ids = []
    if "address_details_eda_ext_n" in data:
        for address_detail in data["address_details_eda_ext_n"]:
            if address_detail.get("address_desc_eda_ext") == "Contractor":
                row_ids.append(address_detail.get("row_id_eda_ext"))
    if "address_eda_ext_n" in data:
        for address in data["address_eda_ext_n"]:
            if address.get("fk_address_details_eda_ext") in row_ids:
                vendor_name = address.get("org_name_eda_ext")
                vendor_duns = address.get("orgid_dunsnum_eda_ext")
                vendor_cage = address.get("orgid_cage_eda_ext")
                return vendor_name, vendor_duns, vendor_cage
    return None, None, None


# To populate Sub Vendor
def populate_vendor_sub(data: dict):
    row_id = None
    if "address_details_eda_ext_n" in data:
        for address_detail in data["address_details_eda_ext_n"]:
            if address_detail.get("address_desc_eda_ext") == "Subcontractor":
                row_id = address_detail.get("row_id_eda_ext")
                break
    if "address_eda_ext_n" in data:
        for address in data["address_eda_ext_n"]:
            if address.get("fk_address_details_eda_ext") == row_id:
                sub_vendor_name = address.get("org_name_eda_ext")
                sub_vendor_duns = address.get("orgid_dunsnum_eda_ext")
                sub_vendor_cage = address.get("orgid_cage_eda_ext")
                return sub_vendor_name, sub_vendor_duns, sub_vendor_cage
    return None, None, None


# To populate contract issue office name and contract issue office  Dodaac:
def populate_contract_issue_office_name_and_contract_issue_office_dodaa(data: dict) -> (str,str):
    row_id = None
    if "address_details_eda_ext_n" in data:
        for address_detail in data["address_details_eda_ext_n"]:
            if address_detail.get("address_desc_eda_ext") == "Contract Issuing Office":
                row_id = address_detail.get("row_id_eda_ext")
                break
    if "address_eda_ext_n" in data:
        for address in data["address_eda_ext_n"]:
            if address.get("fk_address_details_eda_ext") == row_id:
                contract_issue_office_name = address.get("org_name_eda_ext")
                contract_issue_office_dodaac = address.get("orgid_dodaac_eda_ext")

                if contract_issue_office_dodaac and contract_issue_office_dodaac.startswith("W"):
                    dodaac_org_type = "army"
                elif contract_issue_office_dodaac and contract_issue_office_dodaac.startswith("N"):
                    dodaac_org_type = "navy"
                elif contract_issue_office_dodaac and contract_issue_office_dodaac.startswith("F"):
                    dodaac_org_type = "airforce"
                elif contract_issue_office_dodaac and contract_issue_office_dodaac.startswith("SP"):
                    dodaac_org_type = "dla"
                elif contract_issue_office_dodaac and contract_issue_office_dodaac.startswith("M"):
                    dodaac_org_type = "marinecorps"
                else:
                    dodaac_org_type = "estate"

                return contract_issue_office_name,contract_issue_office_dodaac, dodaac_org_type
    return None, None, None, None


# To populate Signature Dates
def contract_effective_and_signed_date(data: dict) -> (str, str):
    effective_date = None
    signature_date = None
    if "proc_inst_header_details_eda_ext_n" in data:
        for proc_inst_header_detail in data["proc_inst_header_details_eda_ext_n"]:
            if "ko_signature_date_eda_ext" in proc_inst_header_detail:
                signature_date = proc_inst_header_detail.get("ko_signature_date_eda_ext")
    if "proc_effective_date_eda_ext_n" in data:
        for proc_effective_date in data['proc_effective_date_eda_ext_n']:
            if "value_eda_ext" in proc_effective_date:
                effective_date = proc_effective_date.get("value_eda_ext")

    return effective_date, signature_date


# To populate Total Obligated Amount
def populate_total_obligated_amount(data: dict) -> str:
    total_obligated_amount = 0.0
    if "obligated_amounts_eda_ext_n" in data:
        for obligated_amount in data.get('obligated_amounts_eda_ext_n'):
            if "chgtxt_eda_ext" in obligated_amount:
                try:
                    total_obligated_amount = total_obligated_amount + float(obligated_amount.get("obligated_amount_delta_eda_ext"))
                except ValueError:
                    pass
            elif "obligated_amount_eda_ext" in obligated_amount:
                try:
                    total_obligated_amount = total_obligated_amount + float(obligated_amount.get("obligated_amount_eda_ext"))
                except ValueError:
                    pass
    return total_obligated_amount


# To Populate NAICS
def populate_naics(data: dict) -> str:
    if "refnum_eda_ext_n" in data:
        for refnum in data['refnum_eda_ext_n']:
            if "ref_desc_eda_ext" in refnum:
                if refnum['ref_desc_eda_ext'] == "North American Industry Classification System (NAICS)":
                    if "ref_value_eda_ext" in refnum:
                        return refnum.get("ref_value_eda_ext")
    return None

