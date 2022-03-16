import os

# this module's path
MODULE_PATH: str = os.path.dirname(os.path.abspath(__file__))
# input jsonschema spec path
INPUT_SPEC_PATH: str = os.path.join(MODULE_PATH, 'input_spec.json')
# output jsonschema spec path
OUTPUT_SPEC_PATH: str = os.path.join(MODULE_PATH, 'output_spec.json')
#directory where CA certificates are stored
CERTIFICATE_DIR: str = os.path.join(MODULE_PATH, "certificates")
