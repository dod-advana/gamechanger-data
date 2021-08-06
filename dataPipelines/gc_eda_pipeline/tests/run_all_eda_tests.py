import unittest

from dataPipelines.gc_eda_pipeline.tests.metadata.test_metadata_util import TestTitle
from dataPipelines.gc_eda_pipeline.tests.metadata.test_syn_extract_json import TestSYNMetadata
from dataPipelines.gc_eda_pipeline.tests.metadata.test_pds_extract_json import TestMPDSetadata
import os


class EDATest(unittest.TestCase):

    def run_test(self):
        title_tests_suite = unittest.TestLoader().loadTestsFromTestCase(TestTitle)
        syn_metadata_tests_suite = unittest.TestLoader().loadTestsFromTestCase(TestSYNMetadata)
        pds_metadata_tests_suite = unittest.TestLoader().loadTestsFromTestCase(TestMPDSetadata)

        all_tests = unittest.TestSuite([title_tests_suite, syn_metadata_tests_suite, pds_metadata_tests_suite])

        unittest.TextTestRunner(verbosity=4).run(all_tests)


if __name__ == '__main__':
    eda_test = EDATest()
    eda_test.run_test()

