import os
from pathlib import Path
from selenium import webdriver

BASE_SOURCE_URL: str = 'https://www.e-publishing.af.mil/Product-Index/#/?view=pubs&orgID=10141&catID=1&series=-1&modID=449&tabID=131'
MODULE_PATH: str = os.path.dirname(os.path.abspath(__file__))
SOURCE_SAMPLE_DIR: str = os.path.join(MODULE_PATH, 'source_sample')
OUTPUT_SAMPLE_DIR: str = os.path.join(MODULE_PATH, 'output_sample')


def get_json_output_sample() -> str:
    with open(next(Path(OUTPUT_SAMPLE_DIR).glob('*.json')), 'r') as f:
        return f.read()


# open web client
options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-gpu')
options.add_argument('--start-maximized')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-setuid-sandbox')
driver = webdriver.Chrome(options=options)