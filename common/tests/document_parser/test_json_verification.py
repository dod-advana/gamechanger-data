
from common.document_parser import validators
import tempfile
from pathlib import Path
from common.tests import PACKAGE_OCR_PDF_PATH
from common.document_parser.cli import pdf_to_json
import shutil


def test_json_schema():
    with tempfile.TemporaryDirectory() as tmpdir:

        test_pdf_path = Path(PACKAGE_OCR_PDF_PATH, "acg_100.fake.pdf")
        test_json_path = Path(tmpdir, test_pdf_path.stem + ".json")

        src_dir_path = Path(tmpdir).resolve()
        dst_dir_path = Path(tmpdir).resolve()

        # put pdf in src dir
        shutil.copy(test_pdf_path, tmpdir)

        # parse
        pdf_to_json(
            parser_path="common.document_parser.parsers.policy_analytics.parse::parse",
            source=str(src_dir_path),
            destination=str(dst_dir_path)
        )

        assert validators.verify(test_json_path)