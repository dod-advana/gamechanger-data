import unittest
import json
from dataPipelines.gc_eda_pipeline.metadata.pds_extract_json import extract_pds
from dataPipelines.gc_eda_pipeline.metadata.pds_extract_json import populate_modification, populate_award_id_referenced_idv, populate_address, populate_vendor, populate_contract_issue_office_name_and_contract_issue_office_dodaa, populate_vendor_sub, contract_effective_and_signed_date, populate_total_obligated_amount, populate_naics
from dataPipelines.gc_eda_pipeline.metadata.metadata_util import format_supplementary_data
from dataPipelines.gc_eda_pipeline.utils.eda_utils import read_extension_conf
import os
import copy

# GET gc_eda_2021_test_current/_search
# {
#   "query": {
#     "bool": {
#       "must": [
#         {
#           "term": {
#             "s3_loc_eda_ext.keyword": {
#               "value": "s3://advana-data-zone/eda/pds/N0018910DZ0271018/EDAPDS-022471CEB5AB12BEE05400215A9BA3BA-N0018910DZ027-1018-empty-empty-PDS-2014-09-03.json"
#             }
#           }
#         }
#       ]
#     }
#   }
# }

class TestMPDSetadata(unittest.TestCase):
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    # GC_APP_CONFIG_EXT_NAME = os.environ["GC_APP_CONFIG_EXT_NAME"] = BASE_DIR + "/test_files/eda_test_conf.json"
    data = None
    data_conf_filter = None
    extensions_metadata = {}

    def setUp(self) -> None:
        with open(self.BASE_DIR + "/test_files/" + "TEST_PDS.json") as json_file:
            self.raw_data = json.load(json_file)
        self.data_conf_filter = read_extension_conf()

        self.data = copy.deepcopy(self.raw_data)
        date_fields_l = self.data_conf_filter['eda']['sql_filter_fields']['date']
        format_supplementary_data(self.data, date_fields_l)

        self.extensions_metadata["pds_contract_eda_ext"] = "N0018910DZ027"
        self.extensions_metadata["pds_ordernum_eda_ext"] = "1018"

    def test_modification_number(self):
        modification_number = populate_modification(self.data)
        self.assertEqual(modification_number, "Award")

    def test_populate_award_id_referenced_idv(self):
        award_id, referenced_idv = populate_award_id_referenced_idv(self.data, self.extensions_metadata)
        self.assertEqual(award_id, "1018")
        self.assertEqual(referenced_idv, "N0018910DZ027")

    def test_populate_address(self):
        contract_admin_agency_name, contract_admin_office_dodaac, contract_payment_office_name, contract_payment_office_dodaac = populate_address(
            self.data)

        self.assertEqual(contract_admin_agency_name, "DCMA VIRGINIA")
        self.assertEqual(contract_admin_office_dodaac, "S2404A")
        self.assertEqual(contract_payment_office_name, "DFAS COLUMBUS CENTER")
        self.assertEqual(contract_payment_office_dodaac, "HQ0338")

    def test_populate_vendor(self):
        vendor_name, vendor_duns, vendor_cage = populate_vendor(self.data)
        self.assertEqual(vendor_name, "BOOZ ALLEN HAMILTON INC.")
        self.assertEqual(vendor_duns, "006928857")
        self.assertEqual(vendor_cage, "17038")

    def test_populate_contract_issue_office_name_and_contract_issue_office_dodaa(self):
        contract_issue_office_name, contract_issue_office_dodaac, dodaac_org_type = populate_contract_issue_office_name_and_contract_issue_office_dodaa(
            self.data)
        self.assertEqual(contract_issue_office_name, "NAVSUP FLC NORFOLK PHILADELPHIA OFFICE")
        self.assertEqual(contract_issue_office_dodaac, "N00189")
        self.assertEqual(dodaac_org_type, "navy")

    # No files contain vendor_sub data
    def test_populate_vendor_sub(self):
        sub_vendor_name, sub_vendor_duns, sub_vendor_cage = populate_vendor_sub(self.data)
        self.assertEqual(sub_vendor_name, None)
        self.assertEqual(sub_vendor_duns, None)
        self.assertEqual(sub_vendor_cage, None)

    def test_contract_effective_and_signed_date(self):
        effective_date, signature_date = contract_effective_and_signed_date(self.data)
        self.assertEqual(effective_date, "2014-08-28")
        self.assertEqual(signature_date, "2014-09-02")

    def test_populate_total_obligated_amount(self):
        total_obligated_amount = populate_total_obligated_amount(self.data)
        self.assertEqual(total_obligated_amount, 250000.0)

    def test_extract_pds(self):
        extracted_data = extract_pds(self.data_conf_filter, self.raw_data, self.extensions_metadata)
        extracted_data_eda_n = extracted_data.get('extracted_data_eda_n')
        self.assertEqual(extracted_data_eda_n.get('modification_number_eda_ext'), 'Award')
        self.assertEqual(extracted_data_eda_n.get('award_id_eda_ext'), '1018')
        self.assertEqual(extracted_data_eda_n.get('vendor_name_eda_ext'), 'BOOZ ALLEN HAMILTON INC.')
        self.assertEqual(extracted_data_eda_n.get('vendor_duns_eda_ext'), '006928857')
        self.assertEqual(extracted_data_eda_n.get('contract_issue_office_majcom_eda_ext'), 'Naval Supply Systems Command Headquarters')


if __name__ == '__main__':
    unittest.main()
