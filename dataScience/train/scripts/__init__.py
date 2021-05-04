import os

# abs path to this package
PACKAGE_PATH: str = os.path.dirname(os.path.abspath(__file__))
DATA_PATH: str = os.path.join(PACKAGE_PATH, 'data')
NLTK_DATA_PATH: str = os.path.join(DATA_PATH, 'nltk_data')
AGENCY_DATA_PATH: str = os.path.join(DATA_PATH, 'agencies')
