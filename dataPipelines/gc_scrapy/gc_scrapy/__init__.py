import os
from pathlib import Path

# this module's path
MODULE_PATH: str = os.path.dirname(os.path.abspath(__file__))
# input jsonschema spec path
INPUT_SPEC_PATH: str = os.path.join(MODULE_PATH, 'input_spec.json')
# output jsonschema spec path
OUTPUT_SPEC_PATH: str = os.path.join(MODULE_PATH, 'output_spec.json')
#directory where CA certificates are stored
CERTIFICATE_DIR: str = os.path.join(MODULE_PATH, "certificates")


MODULE_PATH: str = os.path.dirname(os.path.abspath(__file__))
SOURCE_SAMPLE_DIR: str = os.path.join(MODULE_PATH, "source_sample")
OUTPUT_SAMPLE_DIR: str = os.path.join(MODULE_PATH, "output_sample")

OUTPUT_FOLDER_NAME = "spider_output"

def get_json_output_sample() -> str:
    with open(next(Path(OUTPUT_SAMPLE_DIR).glob('*.json')), 'r') as f:
        return f.read()