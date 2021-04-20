import bs4
import re
import os
import requests
import json
import datetime
from typing import Iterable
import time

from selenium import webdriver
from pathlib import Path
from selenium.webdriver.support.ui import WebDriverWait  # for implicit and explict waits
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains

from dataPipelines.gc_crawler.requestors import MapBasedPseudoRequestor
from dataPipelines.gc_crawler.exec_model import Crawler, Parser, Pager
from dataPipelines.gc_crawler.data_model import Document, DownloadableItem

from . import SOURCE_SAMPLE_DIR, BASE_SOURCE_URL, driver


def extract_elements(table, type_prefix, base_url, driver):
    """helper function for the parse to create the document"""
    rows = table.find_all('tr')
    documents = []
    for row in rows[1:]:
        columns = row.find_all('td')
        doc_title = columns[1].text.strip()
        doc_num = columns[0].text.strip().replace(" ","_").replace(u'\u200b', '')
        if not bool(re.search(r'\d', doc_num)):
            continue
        if "RESPERSMAN" in driver.current_url:
            type_suffix = ""
        elif '.' in doc_num:
            type_suffix = "INST"
        else:
            type_suffix = "NOTE"
        doc_type = type_prefix + type_suffix
        doc_name = doc_type + " " + doc_num
        if re.search(r'\(\d\)', doc_title):
            doc_name_suffix = re.split('\(', doc_title)
            doc_name_suffix = re.split('\)', doc_name_suffix[1])
            if doc_name_suffix[0].strip() != "":
                doc_name = doc_name + '_' + doc_name_suffix[0]
            if len(doc_name_suffix) > 1 and doc_name_suffix[1].strip() != "":
                doc_name = doc_name + '_' + doc_name_suffix[1].strip().replace(" ","_")
        publication_date = "N/A"
        cac_login_required = False

        source_page_url = driver.current_url
        pdf_url = base_url + columns[2].find('a')['href']
        pdf_di = DownloadableItem(
            doc_type='pdf',
            web_url=pdf_url
        )
        version_hash_fields = {
            "doc_name": doc_name,
            "doc_title": doc_title
        }
        doc = Document(
            doc_name=doc_name.strip(),
            doc_title=doc_title.strip(),
            doc_num=doc_num.strip(),
            doc_type=doc_type.strip(),
            publication_date=publication_date,
            cac_login_required=cac_login_required,
            crawler_used="navy_reserves",
            source_page_url=source_page_url,
            version_hash_raw_data=version_hash_fields,
            downloadable_items=[pdf_di]
        )
        documents.append(doc)
    return documents



class NavyReservesPager(Pager):
    """Pager for Navy Reserves crawler"""

    def iter_page_links(self) -> Iterable[str]:
        """Iterator for page links"""

        r = requests.get(self.starting_url)
        soup = bs4.BeautifulSoup(r.content, features="html.parser")

        # get target column of list items
        resources = soup.find_all("ul", attrs={'class': 'dropdown-menu'})[3].find('ul')

        for resource in resources.find_all('a'):
            if 'Message' not in resource.text:
                yield resource['href']


class NavyReservesParser(Parser):
    """Parser for Navy Reserves pubs crawler"""

    def parse_docs_from_page(self, page_url: str, page_text: str) -> Iterable[Document]:
        """Parse document objects from page of text"""
        parsed_docs = []
        # parse html response
        base_url = 'https://www.navyreserve.navy.mil/'
        if "Instruction" in page_url or "Notice" in page_url:
            type_prefix = "COMNAVRESFORCOM"
        if "RESPERSMAN" in page_url:
            type_prefix = "RESPERSMAN"
        driver.get(page_url)

        WebDriverWait(driver, 20).until(ec.presence_of_element_located((By.XPATH, "//*[@class='dropdown-menu']")))
        html = driver.execute_script("return document.documentElement.outerHTML")
        soup = bs4.BeautifulSoup(html, features="html.parser")

        data_tables = soup.find_all('table', attrs={'class': 'dnnGrid'})
        paging_tables = soup.find_all('table', attrs={'class': 'PagingTable'})

        for i in range(len(data_tables)):
            next_page_number = 0
            while True:
                parsed_docs.extend(extract_elements(data_tables[i], type_prefix, base_url, driver))
                if len(paging_tables[i].find_all('a')) > 0 and paging_tables[i].find_all('a')[-1].text == "Last":
                    time.sleep(2)
                    nexter = paging_tables[i].find_all('a')[-2]['href']
                    if next_page_number != int(re.findall(r'\d+', nexter)[-1]):
                        next_page_number = int(re.findall(r'\d+', nexter)[-1])
                    else:
                        print("JavaScript Error.. Try Again Later")
                        break
                    next_button = WebDriverWait(driver, 20).until(
                        ec.element_to_be_clickable((By.XPATH, '//a[@href="' + nexter + '"]'))).click()
                    time.sleep(2)
                    html = driver.execute_script("return document.documentElement.outerHTML")
                    soup = bs4.BeautifulSoup(html, features="html.parser")
                    data_tables = soup.find_all('table', attrs={'class': 'dnnGrid'})
                    paging_tables = soup.find_all('table', attrs={'class': 'PagingTable'})
                else:
                    break

        return parsed_docs


class NavyReservesCrawler(Crawler):
    """Crawler for the example web scraper"""
    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            **kwargs,
            pager=NavyReservesPager(
                starting_url=BASE_SOURCE_URL
            ),
            parser=NavyReservesParser()
        )


class FakeNavyReservesCrawler(Crawler):
    """Navy Reserves crawler that just uses stubs and local source files"""
    def __init__(self, *args, **kwargs):
        with open(os.path.join(SOURCE_SAMPLE_DIR, 'navy_reserves.html')) as f:
            default_text = f.read()

        super().__init__(
            *args,
            **kwargs,
            pager=NavyReservesPager(
                requestor=MapBasedPseudoRequestor(
                    default_text=default_text
                ),
                starting_url=BASE_SOURCE_URL
            ),
            parser=NavyReservesParser()
        )
