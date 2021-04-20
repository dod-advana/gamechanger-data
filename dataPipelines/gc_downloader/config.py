from pathlib import Path
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
import typing as t

SUPPORTED_FILE_EXTENSIONS = [
    ".pdf",
    ".zip"
]


class Config:
    default_manifest_name = "manifest.json"
    default_dead_queue_name = "dead_queue.json"

    @ staticmethod
    def get_driver(output_dir: t.Union[Path, str]) -> t.Optional[webdriver.Chrome]:

        output_dir_path = Path(output_dir).absolute()
        output_dir_path.mkdir(exist_ok=True)

        try:
            # First, create the webdriver for all docs
            options = webdriver.ChromeOptions()
            options.add_argument('--headless')
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-gpu")
            options.add_argument("--start-maximized")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-setuid-sandbox")
            options.add_experimental_option('prefs', {
                "download.default_directory": str(output_dir_path),  # Change default directory for downloads
                "download.prompt_for_download": False,  # To auto download the file
                "download.directory_upgrade": True,
                "plugins.always_open_pdf_externally": True  # It will not show PDF directly in chrome
            })
            driver = webdriver.Chrome(options=options)
        except WebDriverException:
            print("No WebDriver installed or WebDriver not found in the executable path. Cannot run selenium downloads.")
            driver = None

        return driver