import os
from pathlib import Path
from selenium import webdriver

BASE_SOURCE_URL_PAGER = "https://www.govinfo.gov/app/collection"

BASE_SOURCE_URL_CRAWLER = "https://www.govinfo.gov/"
MODULE_PATH: str = os.path.dirname(os.path.abspath(__file__))
SOURCE_SAMPLE_DIR: str = os.path.join(MODULE_PATH, "source_sample")
OUTPUT_SAMPLE_DIR: str = os.path.join(MODULE_PATH, "output_sample")


def get_json_output_sample() -> str:
    with open(next(Path(OUTPUT_SAMPLE_DIR).glob('*.json')), 'r') as f:
        return f.read()

options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument("--no-sandbox")
options.add_argument("--disable-gpu")
options.add_argument("--start-maximized")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-setuid-sandbox")
driver = webdriver.Chrome(options=options)