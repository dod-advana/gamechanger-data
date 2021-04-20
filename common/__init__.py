import os

# this module's path
PACKAGE_PATH: str = os.path.dirname(os.path.abspath(__file__))

# data directory
PACKAGE_DATA_PATH: str = os.path.join(PACKAGE_PATH, "data")

# ocr pdf directory
PACKAGE_DOCUMENT_PARSER_PATH: str = os.path.join(PACKAGE_PATH, "document_parser")
