import bs4
import os
import re
from typing import Iterable

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait  # for implicit and explict waits
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By

from dataPipelines.gc_crawler.requestors import MapBasedPseudoRequestor
from dataPipelines.gc_crawler.exec_model import Crawler, Parser, Pager
from dataPipelines.gc_crawler.data_model import Document, DownloadableItem
from dataPipelines.gc_crawler.utils import abs_url, close_driver_windows_and_quit



from . import SOURCE_SAMPLE_DIR, BASE_SOURCE_URL


class STANAGPager(Pager):
    """Pager for Nato Stanag crawler"""

    def iter_page_links(self) -> Iterable[str]:
        """Iterator for page links"""
        base_url = 'https://nso.nato.int/nso/nsdd/'
        starting_url = base_url + 'ListPromulg.html'

        global driver
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-gpu")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-setuid-sandbox")
        driver = webdriver.Chrome(options=options)
        yield starting_url


class STANAGParser(Parser):
    """Parser for Nato Stanag crawler"""

    def parse_docs_from_page(self, page_url: str, page_text: str) -> Iterable[Document]:
        """Parse document objects from page of text"""

        # parse html response
        pdf_prefix = 'https://nso.nato.int/nso/'
        driver.get(page_url)
        WebDriverWait(driver, 10).until(ec.presence_of_element_located((By.XPATH, "//*[@id='headerSO']")))
        html = driver.execute_script("return document.documentElement.outerHTML")
        soup = bs4.BeautifulSoup(html, features="html.parser")

        parsed_docs = []

        table = soup.find('table', attrs={'id': 'dataSearchResult'})
        rows = table.find_all('tr')

        for row in rows[1:]:
            data = row.find_all('td')
            if "No" not in data[1].text:
                doc_title = data[4].text.splitlines()[1].strip()
                doc_helper = data[2].text.split("Ed:")[0].strip()

                if "STANAG" in doc_helper or"STANREC" in doc_helper:
                    doc_num = doc_helper.split("\n")[1].strip().replace(" ","_")
                    doc_type = doc_helper.split("\n")[0].strip().replace(" ","_")

                else:
                    doc_ = doc_helper.split("\n")[0].strip()
                    doc_num  = doc_.split('-',1)[1].strip().replace(" ","_")
                    doc_type = doc_.split('-',1)[0].strip().replace(" ","_")
                    if len(doc_helper.split())>1:
                        if re.match("^M{0,4}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$", doc_helper.split()[1].strip()):
                            doc_num = doc_num + "_VOL" + doc_helper.split()[1].strip()
                        if re.match("^\d$",doc_helper.split()[1].strip()):
                            doc_num = doc_num + "_PART" + doc_helper.split()[1].strip()

                if len(data[2].text.split("VOL")) > 1:
                    volume = data[2].text.split("VOL")[1].split()[0].strip()
                    doc_num = doc_num + "_VOL" + volume

                if len(data[2].text.split("PART")) > 1:
                    volume = data[2].text.split("PART")[1].split()[0].strip()
                    doc_num = doc_num + "_PART" + volume
                doc_name = doc_type + " " + doc_num
                if doc_name in (o.doc_name for o in parsed_docs) and doc_title in (t.doc_title for t in parsed_docs):
                    #getting rid of duplicates
                    continue

                if len(data[2].text.split("Ed:")) > 1:
                    edition = data[2].text.split("Ed:")[1].strip()
                else:
                    edition = ""

                publication_date = data[5].text.splitlines()[1].strip()
                pdf_suffix = data[4].find('a')
                if pdf_suffix is None:
                    continue
                if "../classDoc.htm" in pdf_suffix['href']:
                    cac_login_required = True
                else:
                    cac_login_required = False

                di = DownloadableItem(
                    doc_type='pdf',
                    web_url=pdf_prefix + pdf_suffix['href'].replace('../', '').replace(" ", "%20")
                )

                crawler_used = "nato_stanag"
                version_hash_fields = {
                    "editions_and_volume": edition,
                    "type": data[1].text
                }
                doc = Document(
                    doc_name=doc_name,
                    doc_title=doc_title,
                    doc_num=doc_num,
                    doc_type=doc_type,
                    publication_date=publication_date,
                    cac_login_required=cac_login_required,
                    crawler_used=crawler_used,
                    source_page_url=page_url.strip(),
                    version_hash_raw_data=version_hash_fields,
                    downloadable_items=[di]
                )
                parsed_docs.append(doc)

        close_driver_windows_and_quit(driver)
        return parsed_docs


class STANAGCrawler(Crawler):
    """Crawler for the example web scraper"""
    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            **kwargs,
            pager=STANAGPager(
                starting_url=BASE_SOURCE_URL
            ),
            parser=STANAGParser()
        )


class FakeSTANAGCrawler(Crawler):
    """Nato Stanag crawler that just uses stubs and local source files"""
    def __init__(self, *args, **kwargs):
        with open(os.path.join(SOURCE_SAMPLE_DIR, 'dod_issuances.html')) as f:
            default_text = f.read()

        super().__init__(
            *args,
            **kwargs,
            pager=DoDPager(
                requestor=MapBasedPseudoRequestor(
                    default_text=default_text
                ),
                starting_url=BASE_SOURCE_URL
            ),
            parser=STANAGParser()
        )
