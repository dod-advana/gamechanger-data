import uuid


def process_procurement(data: dict) -> dict:
    data_value = {
        'id': str(uuid.uuid4()),
        'Service_Agency': data.get('P40-07_Org_Code'),
        'Service_Agency_Description': data.get('P40-06_Organization'),
        'Position': data.get('P40-05_BudgetCycle'),
        'Position_Year': data.get('P40-04_BudgetYear'),
        'PB_Submission_Date': None,
        'Appropriation': data.get('P40-08_Appn_Number'),
        'Appropriation_Title': data.get('P40-09_Appn_Title'),
        'Budget_Activity': data.get('P40-10_BA_Number'),
        'Budget_Activity_Title': data.get('P40-11_BA_Title'),
        'Budget_Line_Item': data.get('P40-01_LI_Number'),
        'Budget_Line_Item_Title': data.get('P40-02_LI_Title'),
        'P1_Line_Number': data.get('P40-03_P1_LineNumber'),
        'All_Prior_Years_Amt': data.get('P40-76_TOA_APY'),
        'Prior_Year_Amt': data.get('P40-77_TOA_PY'),
        'Current_Year_Amt': data.get('P40-78_TOA_CY'),
        'Budget_Year_1_Total': data.get('PP40-81_TOA_BY1'),
        'Budget_Year_2_Total': None,
        'Budget_Year_3_Total': None,
        'Budget_Year_4_Total': None,
        'Budget_Year_5_Total': None,
        'To_Complete': None, 'Total': None,
        'Program_Description': None,
        'Budget_Justification': None,
        'Program_Element': None,
        'Program_Description_Map': None,
        'Program_Description_Count': None,
        'Budget_Justification_Map': None,
        'Budget_Justification_Count': None,
        'core_ai_label': None,
        'jaic_review_stat': None,
        'jaic_review_notes': None,
        'reviewer': None,
        'source_tag': None,
        'planned_trans_part': None,
        'current_msn_part': None,
        'service_review': None,
        'dj_core_ai_label': None
    }
    return data_value