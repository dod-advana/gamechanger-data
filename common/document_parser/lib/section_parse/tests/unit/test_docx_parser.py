"""Unit tests for the DocxParser class in 
common.document_parser.lib.section_parse.docx_parser.

Note: See section_parse.tests.integration.test_parse for testing
DocxParser.parse().
"""

from unittest import TestCase, main
from collections import defaultdict
from os.path import dirname, join
from docx.text.paragraph import Paragraph
from docx.table import Table
import sys
sys.path.append(dirname(__file__).replace("/section_parse/tests/unit", ""))
from section_parse import DocxParser


class DocxParserTest(TestCase):
    """Unit tests for the DocxParser class in
    common.document_parser.lib.section_parse.docx_parser.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.parser = DocxParser(
            join(dirname(__file__).replace("unit", "data"), "test_utils.docx")
        )
        if len(cls.parser.doc.tables) != 1:
            raise Exception(
                f"SETUP FAILED. There should be exactly 1 Table in the test doc."
            )
        else:
            cls.table = cls.parser.doc.tables[0]

        # Set up for test_iter_block_items().
        cls.expected_table_indices = [25]

    def _check_parser_attr(
        self, attr: str, expected_type, check_type: bool = True
    ):
        fail_msg = "FAILURE: DocxParser initialization. "
        self.assertTrue(
            hasattr(self.parser, attr),
            fail_msg + f"Missing `{attr}` attribute.",
        )
        if check_type:
            self.assertIsInstance(
                getattr(self.parser, attr),
                expected_type,
                fail_msg + f"Attribute `{attr}` has incorrect type.",
            )

    def test_attributes(self):
        """Verify that the DocxParser was initialized with expected attributes."""
        self._check_parser_attr("doc", None, False)
        self._check_parser_attr("blocks", list)
        self._check_parser_attr("space_mode", int)
        self.assertGreater(
            self.parser.space_mode,
            0,
            "`space_mode` attribute should be greater than 0.",
        )

    def test_iter_block_items(self):
        """Verifies iter_block_items()."""
        blocks = list(self.parser.iter_block_items())
        actual_table_indices = []
        unexpected_types = defaultdict(int)

        for i in range(len(blocks)):
            block = blocks[i]
            if isinstance(block, Table):
                actual_table_indices.append(i)
            elif isinstance(block, Paragraph):
                pass
            else:
                unexpected_types[i] = type(block)

        fail_msg = "FAILURE: `test_iter_block_items()`. "
        self.assertEqual(
            actual_table_indices,
            self.expected_table_indices,
            fail_msg + f"Table indices are incorrect. Expected tables at: "
            f"`{self.expected_table_indices}`. Found tables at: "
            f"`{actual_table_indices}`.",
        )
        self.assertTrue(
            len(unexpected_types) == 0,
            fail_msg + f"Unexpected types found: `{unexpected_types}`.",
        )

    def test_flatten_table_without_fixing_order(self):
        """Verifies flatten_table() called with param `should_fix_order=False`."""
        expected_texts = [
            "following: ",
            "5.2.1.2.  Additional functions and activities of DEOMI shall include the ",
        ]

        table_flat = DocxParser.flatten_table(self.table, False)
        for block in table_flat:
            self.assertTrue(
                isinstance(block, Paragraph),
                f"FAILURE: An item in the output of `flatten_table()` is not "
                f"of type Paragraph. The item is: `{block}`.",
            )

        actual_texts = [par.text for par in table_flat]

        self.assertEqual(
            actual_texts,
            expected_texts,
            f"FAILURE for `test_flatten_table_without_fixing_order()`. "
            f"Expected texts were: `{expected_texts}`.\n\n"
            f"Actual texts were: `{actual_texts}`.",
        )

    def test_flatten_table_with_fixing_order(self):
        """Verifies flatten_table() called with param `should_fix_order=True`."""
        expected_texts = [
            "5.2.1.2.  Additional functions and activities of DEOMI shall include the ",
            "following: ",
        ]

        table_flat = DocxParser.flatten_table(self.table, True)
        for block in table_flat:
            self.assertTrue(
                isinstance(block, Paragraph),
                f"FAILURE: An item in the output of `flatten_table()` is not "
                f"of type Paragraph. The item is: `{block}`.",
            )

        actual_texts = [par.text for par in table_flat]

        self.assertEqual(
            actual_texts,
            expected_texts,
            f"FAILURE for `test_flatten_table_with_fixing_order()`. "
            f"Expected texts were: `{expected_texts}`.\n\n"
            f"Actual texts were: `{actual_texts}`.",
        )


if __name__ == "__main__":
    main(failfast=True)
