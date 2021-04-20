import bs4
import re
import os
import requests
from typing import Iterable
from time import sleep

from dataPipelines.gc_crawler.requestors import MapBasedPseudoRequestor
from dataPipelines.gc_crawler.exec_model import Crawler, Parser, Pager
from dataPipelines.gc_crawler.data_model import Document, DownloadableItem
from dataPipelines.gc_crawler.utils import close_driver_windows_and_quit
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait  # for implicit and explict waits
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.action_chains import ActionChains

from . import SOURCE_SAMPLE_DIR, BASE_SOURCE_URL, driver


class SECNAVPager(Pager):
    """Pager for SECNAV crawler"""

    def iter_page_links(self) -> Iterable[str]:
        """Iterator for page links"""
        base_url = 'https://www.secnav.navy.mil'
        doni_url = 'https://www.secnav.navy.mil/doni/default.aspx'

        r = requests.get(doni_url)
        soup = bs4.BeautifulSoup(r.content, features="html.parser")

        # get target column of list items
        issuance_list = soup.find_all('a', attrs={'class': 'dynamic'})[:2]

        # extract links
        for link in issuance_list[:2]:
            if not link['href'].startswith('http'):
                url = base_url + link['href']
            else:
                url = link['href']

            yield url


class SECNAVParser(Parser):
    """Parser for SECNAV crawler"""

    def parse_docs_from_page(self, page_url: str, page_text: str) -> Iterable[Document]:
        """Parse document objects from page of text"""

        parsed_docs = []
        # parse html response
        base_url = 'https://www.secnav.navy.mil'


        type_suffix = ""
        if page_url.__contains__("instruction"):
            type_suffix = "INST"
        if page_url.__contains__("notice"):
            type_suffix = "NOTE"

        last_page = ""
        try:
            driver.get(page_url)
            WebDriverWait(driver, 20).until(ec.presence_of_element_located((By.XPATH, "//*[@class='dynamic']")))
        except TimeoutException as e:
            print("Error: " + e)
            print("Trying again...")
            try:
                driver.get(page_url)
                WebDriverWait(driver, 20).until(ec.presence_of_element_located((By.XPATH, "//*[@class='dynamic']")))
            except TimeoutException as e:
                print("Error: " + e)
                print(page_url + "cannot be scrapped.")
                return parsed_docs
        while True:
            while last_page == driver.current_url:
                sleep(1)
            html = driver.execute_script("return document.documentElement.outerHTML")
            soup = bs4.BeautifulSoup(html, features="html.parser")
            last_page = driver.current_url

            table = soup.find('table', attrs={'class': 'ms-listviewtable'})
            rows = table.find_all('tr')
            for r in rows[1:]:
                td = r.find_all('td')
                doc_name = td[0].text + type_suffix + " " + td[1].text
                doc_title = td[2].text
                doc_num = td[1].text
                doc_type = td[0].text + type_suffix
                publication_date = td[3].text
                pdf_url = base_url + td[1].find('a')['href'].replace(" ", '%20')
                pdf_di = DownloadableItem(
                    doc_type='pdf',
                    web_url=pdf_url
                )
                source_page_url = driver.current_url
                cac_login_required = re.match('^[A-Za-z]', doc_num) != None
                version_hash_fields = {
                    "active_status": td[4].text,
                    "sponsor": td[5].text,
                    "form": td[6].text,
                    "reports_control_symbol": td[7].text,
                    "pages": td[8].text,
                    "cancelled_date": td[9].text
                }
                doc = Document(
                    doc_name=doc_name.strip(),
                    doc_title=doc_title.strip(),
                    doc_num=doc_num.strip(),
                    doc_type=doc_type.strip(),
                    publication_date=publication_date,
                    cac_login_required=cac_login_required,
                    crawler_used="secnav_pubs",
                    source_page_url=source_page_url,
                    version_hash_raw_data=version_hash_fields,
                    downloadable_items=[pdf_di]
                )
                parsed_docs.append(doc)

            if (soup.find('td', attrs={'id': 'pagingWPQ3next'}) != None):
                try:
                    next_button = WebDriverWait(driver, 20).until(
                        ec.presence_of_element_located((By.XPATH, "//*[@id='pagingWPQ3next']")))
                    ActionChains(driver).move_to_element(next_button).perform()
                    next_button.click()
                except WebDriverException as e:
                    print("Error: " + e)
                    print("Cannot go to the next page.")
                    break
            else:
                break

        return parsed_docs


class SECNAVCrawler(Crawler):
    """Crawler for the example web scraper"""
    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            **kwargs,
            pager=SECNAVPager(
                starting_url=BASE_SOURCE_URL
            ),
            parser=SECNAVParser()
        )


class FakeSECNAVCrawler(Crawler):
    """SECNAV crawler that just uses stubs and local source files"""
    def __init__(self, *args, **kwargs):
        with open(os.path.join(SOURCE_SAMPLE_DIR, 'secnav_pubs.html')) as f:
            default_text = f.read()

        super().__init__(
            *args,
            **kwargs,
            pager=SECNAVPager(
                requestor=MapBasedPseudoRequestor(
                    default_text=default_text
                ),
                starting_url=BASE_SOURCE_URL
            ),
            parser=SECNAVParser()
        )
