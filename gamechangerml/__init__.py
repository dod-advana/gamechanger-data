import os

# abs path to this package
PACKAGE_PATH: str = os.path.dirname(os.path.abspath(__file__))
REPO_PATH: str = os.path.abspath(os.path.join(PACKAGE_PATH, ".."))
DATA_PATH: str = os.path.join(PACKAGE_PATH, "data")
MODEL_PATH: str = os.path.join(PACKAGE_PATH, "models")
CORPUS_PATH: str = os.environ.get(
    "LOCAL_CORPUS_PATH", default=os.path.join(PACKAGE_PATH, "corpus")
)
NLTK_DATA_PATH: str = os.path.join(DATA_PATH, "nltk_data")
AGENCY_DATA_PATH: str = os.path.join(DATA_PATH, "agencies")
