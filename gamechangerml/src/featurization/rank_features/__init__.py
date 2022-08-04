import os

# abs path to this package
PACKAGE_PATH: str = os.path.dirname(os.path.abspath(__file__))
GENERATED_FILES_PATH: str = os.path.join(PACKAGE_PATH, 'generated_files')