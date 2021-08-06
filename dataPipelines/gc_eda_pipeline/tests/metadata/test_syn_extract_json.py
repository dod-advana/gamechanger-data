import json
import unittest

from dataPipelines.gc_eda_pipeline.metadata.syn_extract_json import populate_modification, populate_award_id_referenced_idv, populate_total_obligated_amount, header_psc, contract_effective_and_signed_date, contract_agency_name_and_issuing_office_dodaac, populate_vendor, populate_address, extract_syn
from dataPipelines.gc_eda_pipeline.metadata.metadata_util import format_supplementary_data
from dataPipelines.gc_eda_pipeline.utils.eda_utils import read_extension_conf
from dataPipelines.gc_eda_pipeline.conf import Conf
import os
import copy


class TestSYNMetadata(unittest.TestCase):

    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    # GC_APP_CONFIG_EXT_NAME = os.environ["GC_APP_CONFIG_EXT_NAME"] = BASE_DIR + "/test_files/eda_test_conf.json"
    data = None
    data_conf_filter = None
    extensions_metadata = {}

    def setUp(self) -> None:
        self.BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

        # ex_file_s3_path = "/gamechanger/projects/eda/test/test_files/EDASYNOPSIS-5881BECADC79432FE05400215A9BA3BA-FA807514D0016-0022-empty-06-SynopsisSPS-2017-09-06.json"
        # self.raw_data = json.loads(Conf.s3_utils.object_content(object_path=ex_file_s3_path))
        # self.raw_data = json.loads(self.raw_data)
        with open(self.BASE_DIR + "/test_files/" + "TEST_SYN.json") as json_file:
            self.raw_data = json.load(json_file)

        self.data = copy.deepcopy(self.raw_data)
        self.data_conf_filter = read_extension_conf()
        date_fields_l = self.data_conf_filter['eda']['sql_filter_fields']['date']
        format_supplementary_data(self.data, date_fields_l)

    def test_populate_modification(self):
        modification_number = populate_modification(self.data)
        self.assertEqual(modification_number, "07")

    def test_populate_award_id_referenced_idv(self):
        award_id, referenced_idv = populate_award_id_referenced_idv(self.data)
        self.assertEqual(award_id, "0022")
        self.assertEqual(referenced_idv, "FA807514D0016")

    def test_contract_payment_office_dodaac(self):
        contract_admin_agency_name, contract_admin_office_dodaac, contract_payment_office_name, contract_payment_office_dodaac = populate_address(
            self.data)
        self.assertEqual(contract_admin_agency_name, "DCMA SPRINGFIELD")
        self.assertEqual(contract_admin_office_dodaac, "S3101A")
        self.assertEqual(contract_payment_office_name, "DFAS-COLUMBUS-DSFDS")
        self.assertEqual(contract_payment_office_dodaac, "JIDLS")

    def test_populate_vendor(self):
        vendor_name, vendor_duns, vendor_cage = populate_vendor(self.data)
        self.assertEqual(vendor_name, "Booz Allen Hamilton Inc.")
        self.assertEqual(vendor_duns, "R32432R4R")
        self.assertEqual(vendor_cage, "17038")

    def test_contract_agency_name_and_issuing_office_dodaac(self):
        contract_issue_office_name, contract_issue_office_dodaac, dodaac_org_type = contract_agency_name_and_issuing_office_dodaac(
            self.data)
        self.assertEqual(contract_issue_office_name, "AFICA/KD")
        self.assertEqual(contract_issue_office_dodaac, "FA3453")

    def test_contract_effective_and_signed_date(self):
        effective_date, signature_date = contract_effective_and_signed_date(self.data)
        self.assertEqual(effective_date, "2023-08-17")
        self.assertEqual(signature_date, None)

    def test_header_psc(self):
        psc_on_contract_header = header_psc(self.data)
        self.assertEqual(psc_on_contract_header, None)

    def test_populate_total_obligated_amount(self):
        total_obligated_amount = populate_total_obligated_amount(self.data, False)
        self.assertEqual(total_obligated_amount, 23492)

    def test_extract_syn(self):
        extracted_data = extract_syn(data_conf_filter=self.data_conf_filter, data=self.raw_data)
        extracted_data_eda_n = extracted_data.get('extracted_data_eda_n')
        self.assertEqual(extracted_data_eda_n.get('modification_number_eda_ext'), '07')
        self.assertEqual(extracted_data_eda_n.get('award_id_eda_ext'), '0022')
        self.assertEqual(extracted_data_eda_n.get('referenced_idv_eda_ext'), 'FA807514D0016')
        self.assertEqual(extracted_data_eda_n.get('contract_admin_office_dodaac_eda_ext'), 'S3101A')
        self.assertEqual(extracted_data_eda_n.get('vendor_name_eda_ext'), 'Booz Allen Hamilton Inc.')