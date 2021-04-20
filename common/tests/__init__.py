import os

# this module's path
PACKAGE_PATH: str = os.path.dirname(os.path.abspath(__file__))

# data directory
PACKAGE_DATA_PATH: str = os.path.join(PACKAGE_PATH, "data")

# ocr pdf directory
PACKAGE_OCR_PDF_PATH: str = os.path.join(PACKAGE_DATA_PATH, "ocr_pdf")
