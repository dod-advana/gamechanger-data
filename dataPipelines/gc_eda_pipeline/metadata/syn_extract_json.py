from dataPipelines.gc_eda_pipeline.metadata.metadata_util import format_supplementary_data


def extract_syn(data_conf_filter: dict, data: dict):
    date_fields_l = data_conf_filter['eda']['sql_filter_fields']['date']
    extracted_data_eda_n = {}
    format_supplementary_data(data, date_fields_l)

    modification_number = populate_modification(data)
    if modification_number:
        extracted_data_eda_n["modification_number_eda_ext"] = modification_number

    award_id, referenced_idv = populate_award_id_referenced_idv(data)
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

    contracting_agency_name, contract_issuing_office_dodaac, dodaac_org_type = contract_agency_name_and_issuing_office_dodaac(data)
    if contracting_agency_name:
        extracted_data_eda_n["contracting_agency_name_eda_ext"] = contracting_agency_name
    if contract_issuing_office_dodaac:
        extracted_data_eda_n["contract_issuing_office_dodaac_eda_ext"] = contract_issuing_office_dodaac
    if dodaac_org_type:
        extracted_data_eda_n["dodaac_org_type_eda_ext"] = dodaac_org_type

    effective_date, signature_date = contract_effective_and_signed_date(data)
    if effective_date:
        extracted_data_eda_n["effective_date_eda_ext_dt"] = effective_date
    if signature_date:
        extracted_data_eda_n["signature_date_eda_ext_dt"] = signature_date

    psc_on_contract_header = header_psc(data)
    if psc_on_contract_header:
        extracted_data_eda_n["psc_on_contract_header_eda_ext"] = psc_on_contract_header

    is_award = False
    if modification_number == "Award":
        is_award = True

    total_obligated_amount = populate_total_obligated_amount(data, is_award)
    if total_obligated_amount:
        extracted_data_eda_n["total_obligated_amount_eda_ext_f"] = total_obligated_amount

    return {"extracted_data_eda_n": extracted_data_eda_n}


# To populate Modifications
def populate_modification(data: dict):

    if "metadata_eda_ext_n" in data:
        metadata = data.get("metadata_eda_ext_n")
        modification_number = metadata.get("modification_eda_ext")
        if modification_number:
            return modification_number
        else:
            return "Award"


# To populate Award ID, ReferencedIDV
def populate_award_id_referenced_idv(data: dict) -> (str, str):
    award_id = None
    referenced_idv = None
    order_number = None
    contract_number = None
    if "syn_contract_eda_ext_n" in data:
        for syn_contract in data.get("syn_contract_eda_ext_n"):
            if syn_contract.get("delivery_order_number_eda_ext"):
                order_number = syn_contract.get("delivery_order_number_eda_ext")
            if syn_contract.get("contract_number_eda_ext"):
                contract_number = syn_contract.get("contract_number_eda_ext")
            if order_number and contract_number:
                referenced_idv = syn_contract.get("contract_number_eda_ext")
                award_id = syn_contract.get("delivery_order_number_eda_ext")
            elif order_number and contract_number is None:
                award_id = syn_contract.get("delivery_order_number_eda_ext")
            elif order_number is None and contract_number:
                award_id = syn_contract.get("contract_number_eda_ext")
    return award_id, referenced_idv


# To populate address fields
def populate_address(data: dict) -> (str, str, str, str):
    contract_admin_agency_name = None
    contract_admin_office_dodaac = None
    contract_payment_office_name = None
    contract_payment_office_dodaac = None
    if "syn_contract_eda_ext_n" in data:
        for contract in data.get("syn_contract_eda_ext_n"):
            if contract.get("admin_org_dodaac_eda_ext"):
                contract_admin_office_dodaac = contract.get("admin_org_dodaac_eda_ext")
            if contract.get("admin_org_name_eda_ext"):
                contract_admin_agency_name = contract.get("admin_org_name_eda_ext")
            if contract.get("pay_org_dodaac_eda_ext"):
                contract_payment_office_dodaac = contract.get("pay_org_dodaac_eda_ext")
            if contract.get("pay_org_name_eda_ext"):
                contract_payment_office_name = contract.get("pay_org_name_eda_ext")
            return contract_admin_agency_name, contract_admin_office_dodaac, contract_payment_office_name, contract_payment_office_dodaac

    return contract_admin_agency_name, contract_admin_office_dodaac, contract_payment_office_name, contract_payment_office_dodaac


# To populate vendor name, vendor duns, and vendor cage
def populate_vendor(data: dict) -> (str, str, str):
    vendor_name = None
    vendor_duns = None
    vendor_cage = None
    if "syn_contract_eda_ext_n" in data:
        for contract in data.get("syn_contract_eda_ext_n"):
            if contract.get("vendor_duns_eda_ext"):
                vendor_duns = contract.get("vendor_duns_eda_ext")
            if contract.get("vendor_name_eda_ext"):
                vendor_name = contract.get("vendor_name_eda_ext")
            if contract.get("vendor_cage_eda_ext"):
                vendor_cage = contract.get("vendor_cage_eda_ext")
            return vendor_name, vendor_duns, vendor_cage
    return vendor_name, vendor_duns, vendor_cage


# To populate contracting agency name and contract issuing office  Dodaac:
def contract_agency_name_and_issuing_office_dodaac(data: dict) -> (str, str):
    contracting_agency_name = None
    contract_issuing_office_dodaac = None
    if "syn_contract_eda_ext_n" in data:
        for contract in data.get("syn_contract_eda_ext_n"):
            if contract.get("buyer_dodaac_eda_ext"):
                contract_issuing_office_dodaac = contract.get("buyer_dodaac_eda_ext")
            if contract.get("buyer_name_eda_ext"):
                contracting_agency_name = contract.get("buyer_name_eda_ext")

            if contract_issuing_office_dodaac and contract_issuing_office_dodaac.startswith("W"):
                dodaac_org_type = "army"
            elif contract_issuing_office_dodaac and contract_issuing_office_dodaac.startswith("N"):
                dodaac_org_type = "navy"
            elif contract_issuing_office_dodaac and contract_issuing_office_dodaac.startswith("F"):
                dodaac_org_type = "airforce"
            elif contract_issuing_office_dodaac and contract_issuing_office_dodaac.startswith("SP"):
                dodaac_org_type = "dla"
            elif contract_issuing_office_dodaac and contract_issuing_office_dodaac.startswith("M"):
                dodaac_org_type = "marinecorps"
            else:
                dodaac_org_type = "estate"

            return contracting_agency_name,contract_issuing_office_dodaac, dodaac_org_type
    return contracting_agency_name, contract_issuing_office_dodaac


# To populate date fields
def contract_effective_and_signed_date(data: dict) -> (str, str):
    effective_date = None
    signature_date = None
    if "syn_contract_eda_ext_n" in data:
        for contract in data.get("syn_contract_eda_ext_n"):
            if contract.get("contract_effective_date_eda_ext_dt"):
                effective_date = contract.get("contract_effective_date_eda_ext_dt")
            if contract.get("contract_signed_date_eda_ext_dt"):
                signature_date = contract.get("contract_signed_date_eda_ext_dt")
            return effective_date, signature_date
    return effective_date, signature_date


# To populate Total Obligated Amount
def populate_total_obligated_amount(data: dict, is_award: bool):
    total_obligated_amount = 0.0
    if "syn_contract_eda_ext_n" in data:
        for syn_contract in data.get("syn_contract_eda_ext_n"):
            if syn_contract.get("total_obligated_amt_eda_ext") and is_award:
                try:
                    total_obligated_amount = total_obligated_amount + float(syn_contract.get("total_obligated_amt_eda_ext"))
                except ValueError:
                    pass
            if syn_contract.get("total_obligated_amt_delta_eda_ext") and not is_award:
                try:
                    total_obligated_amount = total_obligated_amount + float(syn_contract.get("total_obligated_amt_delta_eda_ext"))
                except ValueError:
                    pass
    return total_obligated_amount


# To populate header PSC
def header_psc(data: dict) -> (str):
    psc_on_contract_header = None
    if "syn_contract_eda_ext_n" in data:
        for contract in data.get("syn_contract_eda_ext_n"):
            if contract.get("misc_fsc_eda_ext"):
                psc_on_contract_header = contract.get("misc_fsc_eda_ext")
            return psc_on_contract_header
    return psc_on_contract_header


