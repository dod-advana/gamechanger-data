

def dodaac_org_type_metadata(extracted_data_eda_n: dict) -> str:
    contract_issue_office_dodaac = extracted_data_eda_n.get("contract_issue_office_dodaac_eda_ext")
    vendor_org_hierarchy_eda_n = extracted_data_eda_n.get("vendor_org_hierarchy_eda_n")
    vendor_org_eda_ext_n = vendor_org_hierarchy_eda_n.get("vendor_org_eda_ext_n")
    if vendor_org_eda_ext_n:
        for vendor_org_eda in vendor_org_eda_ext_n:
            dodaac_eda = vendor_org_eda.get('dodaac_eda_ext')
            cgac_agency_name = vendor_org_eda.get('cgac_agency_name_eda_ext')
            if dodaac_eda == contract_issue_office_dodaac:
                return cgac_agency_name

    return None


def contract_issue_office_majcom_metadata(extracted_data_eda_n: dict) -> str:
    contract_issue_office_dodaac = extracted_data_eda_n.get("contract_issue_office_dodaac_eda_ext")
    vendor_org_hierarchy_eda_n = extracted_data_eda_n.get("vendor_org_hierarchy_eda_n")
    vendor_org_eda_ext_n = vendor_org_hierarchy_eda_n.get("vendor_org_eda_ext_n")
    if vendor_org_eda_ext_n:
        for vendor_org_eda in vendor_org_eda_ext_n:
            dodaac_eda = vendor_org_eda.get('dodaac_eda_ext')
            majcom_display_name = vendor_org_eda.get('majcom_display_name_eda_ext')
            if dodaac_eda == contract_issue_office_dodaac:
                return majcom_display_name
