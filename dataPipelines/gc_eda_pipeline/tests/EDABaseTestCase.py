import unittest
import os

from dataPipelines.gc_eda_pipeline.conf import Conf

# Define a common test base for starting servers
class EDABaseTestCase(unittest.TestCase):
    # BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    # GC_APP_CONFIG_EXT_NAME = os.environ["GC_APP_CONFIG_EXT_NAME"] = BASE_DIR + "/test_files/eda_test_conf.json"


    @classmethod
    def setUpClass(cls):
        """On inherited classes, run our `setUp` method"""
        # Inspired via http://stackoverflow.com/questions/1323455/python-unit-test-with-base-and-sub-class/17696807#17696807
        if cls is not EDABaseTestCase and cls.setUp is not EDABaseTestCase.setUp:
            orig_setUp = cls.setUp

            def setUpOverride(self, *args, **kwargs):
                EDABaseTestCase.setUp(self)
                return orig_setUp(self, *args, **kwargs)
            cls.setUp = setUpOverride

    def setUp(self):
        """Do some custom setup"""

        self.abc = True


class ItemCreateTest(EDABaseTestCase):
    def setUp(self):
        """Do more custom setup"""
        self.ddd = "test"

    def test_verify_both_setups_run(self):
        """Test for our current usage"""
        self.assertEqual(self.abc, True)
        self.assertEqual(self.ddd, "test")
