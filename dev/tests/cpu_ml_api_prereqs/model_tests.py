import typing as t
import unittest as ut
import os


class TestSpacyModels(ut.TestCase):

    def test_en_core_web_lg(self):
        import en_core_web_lg
        model = en_core_web_lg.load()
        self.assertIsNotNone(model)

    def test_en_core_web_md(self):
        import en_core_web_md
        model = en_core_web_md.load()
        self.assertIsNotNone(model)