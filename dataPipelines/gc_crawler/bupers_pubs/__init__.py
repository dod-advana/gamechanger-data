import os
from pathlib import Path

BASE_SOURCE_URL: str = 'https://www.mynavyhr.navy.mil/References/Instructions/BUPERS-Instructions/'
MODULE_PATH: str = os.path.dirname(os.path.abspath(__file__))
SOURCE_SAMPLE_DIR: str = os.path.join(MODULE_PATH, "source_sample")
OUTPUT_SAMPLE_DIR: str = os.path.join(MODULE_PATH, "output_sample")


def get_json_output_sample() -> str:
    with open(next(Path(OUTPUT_SAMPLE_DIR).glob('*.json')), 'r') as f:
        return f.read()