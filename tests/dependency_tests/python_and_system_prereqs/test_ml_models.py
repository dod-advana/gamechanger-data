import unittest as ut


class TestSpacyModels(ut.TestCase):

    def test_en_core_web_lg(self):
        import en_core_web_lg
        model = en_core_web_lg.load()
        self.assertIsNotNone(model)

    def test_en_core_web_md(self):
        import en_core_web_md
        model = en_core_web_md.load()
        self.assertIsNotNone(model)

    def test_en_core_web_sm(self):
        import en_core_web_sm
        model = en_core_web_sm.load()
        self.assertIsNotNone(model)