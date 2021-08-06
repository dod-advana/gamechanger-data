import unittest
from dataPipelines.gc_eda_pipeline.metadata.metadata_util import title, mod_identifier
import os


class TestTitle(unittest.TestCase):
    filename_10 = "EDAPDF-4EF2FC8241D364D4E05400215A9BA3BA-SP070003D1380-0180-AY-empty-PDS-2017-05-07.pdf"
    filename_13 = "EDAPDF-ad290457-4e43-4276-9e6e-1587d41196f5-N0018918DZ067-N0018919FZ062-empty-P00004-PDS-2019-11-20.pdf"
    filename_14 = "EDAPDF-fdef6844-193d-4b4f-b5a5-bd52545f027a-N6600116D0071-N6600120F0146-empty-empty-PDS-2019-12-13-test.pdf"
    award_filename = "EDAPDF-BF11A0DC8F952EEBE0440025B3E8F0A7-HQ014710D0011-0005-empty-empty-PDS-2012-05-02.pdf"

    def setUp(self) -> None:
        pass

    def test_title_with_10(self):
        path, filename = os.path.split(self.filename_10)
        filename_without_ext, file_extension = os.path.splitext(filename)
        doc_title = title(filename_without_ext)
        parsed = doc_title.split('-')
        self.assertEqual(len(parsed), 3)
        self.assertEqual(parsed[0], "SP070003D1380")
        self.assertEqual(parsed[1], "0180")
        self.assertEqual(parsed[2], "AY")
        self.assertEqual(doc_title, "SP070003D1380-0180-AY")

    def test_title_with_13(self):
        path, filename = os.path.split(self.filename_13)
        filename_without_ext, file_extension = os.path.splitext(filename)
        doc_title = title(filename_without_ext)
        parsed = doc_title.split('-')
        self.assertEqual(len(parsed), 3)
        self.assertEqual(parsed[0], "N0018918DZ067")
        self.assertEqual(parsed[1], "N0018919FZ062")
        self.assertEqual(parsed[2], "P00004")
        self.assertEqual(doc_title, "N0018918DZ067-N0018919FZ062-P00004")

    def test_title_with_14(self):
        path, filename = os.path.split(self.filename_14)
        filename_without_ext, file_extension = os.path.splitext(filename)
        doc_title = title(filename_without_ext)
        parsed = doc_title.split('-')
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0], "NA")

    def test_mod_identifier(self):
        path, filename = os.path.split(self.filename_10)
        filename_without_ext, file_extension = os.path.splitext(filename)
        mod_identifier_test = mod_identifier(filename_without_ext)
        self.assertEqual(mod_identifier_test, "")

    def test_mod_identifier_base_award(self):
        path, filename = os.path.split(self.award_filename)
        filename_without_ext, file_extension = os.path.splitext(filename)
        mod_identifier_test = mod_identifier(filename_without_ext)
        self.assertEqual(mod_identifier_test, "base_award")


if __name__ == '__main__':
    unittest.main()
