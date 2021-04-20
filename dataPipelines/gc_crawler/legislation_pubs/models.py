import bs4
import os
from typing import Iterable, Tuple
import time

from dataPipelines.gc_crawler.requestors import MapBasedPseudoRequestor
from dataPipelines.gc_crawler.exec_model import Crawler, Parser, Pager
from dataPipelines.gc_crawler.data_model import Document, DownloadableItem

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.by import By
from pathlib import Path
from dataPipelines.gc_crawler.utils import close_driver_windows_and_quit

from . import SOURCE_SAMPLE_DIR, BASE_SOURCE_URL_PAGER, BASE_SOURCE_URL_CRAWLER, driver

class LegislationPager(Pager):

    def __init__(self, starting_url, specific_congress):
        super().__init__(self,
            starting_url
        )
        self.specific_congress = specific_congress
        self.base_url = starting_url
    
    """Pager for Legislation pubs crawler"""
    def iter_page_links(self) -> Iterable[str]:
        """Iterator for page links"""
        pass

    def iter_page_links_with_text(self) -> Iterable[Tuple[str, str]]:

        base_url = self.base_url

        title_list = []
                    
        level1 = '/bills/'+str(self.specific_congress)

        level2_list = []

        driver.get(base_url+level1)
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, "//*[@class='panel-heading BILLSlevel2style closed']")))
        first_html = driver.execute_script("return document.documentElement.outerHTML")
        soup = bs4.BeautifulSoup(first_html, features="html.parser")
        level2_list = [x.get('data-href') for x in soup.find_all(class_='panel-heading BILLSlevel2style closed')]

        for level2 in level2_list:
            driver.get(base_url+level2)
            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, "//*[@class='panel-heading BILLSlevel3style closed']")))
            first_html = driver.execute_script("return document.documentElement.outerHTML")
            soup = bs4.BeautifulSoup(first_html, features="html.parser")
            level3_list = [x.get('data-href') for x in soup.find_all(class_='panel-heading BILLSlevel3style closed')]
            
            for level3 in level3_list:
                driver.get(base_url+level3)
                WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, "//*[@class='panel-heading BILLSlevel3style closed']")))
                first_html = driver.execute_script("return document.documentElement.outerHTML")
                soup = bs4.BeautifulSoup(first_html, features="html.parser")
                title_list += soup.find_all(class_='btn btn-sm btn-format spa-href')

        for item in title_list:
            yield ("https://www.govinfo.gov" + item.get('href'), "")


class LegislationParser(Parser):
    """Parser for Legislation Publication crawler"""

    def parse_docs_from_page(self, page_url: str, page_text: str) -> Iterable[Document]:
        """Parse document objects from page of text"""

        base_url = BASE_SOURCE_URL_CRAWLER

        incoming_url = page_url
        parsed_docs = []
        try:
            driver.get(incoming_url)
            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, "//*[@class='fw-tab-content']")))
        except TimeoutException:
                # reload once if the page fails to load again skip
                try:
                    driver.get(incoming_url)
                    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, "//*[@class='fw-tab-content']")))
                except TimeoutException:
                    return []
        
        time.sleep(.5)
        medium_delay = 3
        try:
            first_html = driver.execute_script("return document.documentElement.outerHTML")
            soup = bs4.BeautifulSoup(first_html, features="html.parser")
            side_panel = soup.find(class_='panel panel-transparent')
            pdf_url = side_panel.find_all('a')[0]['href'][2:]
            detail_area = soup.find("div", {"id": "accMetadata"}).find_all("div", {"class":"row"})
        except NoSuchElementException:
            try:
                # Giving it some more time actually load, if not will by pass for this.
                time.sleep(medium_delay)
                first_html = driver.execute_script("return document.documentElement.outerHTML")
                soup = bs4.BeautifulSoup(first_html, features="html.parser")
                side_panel = soup.find(class_='panel panel-transparent')
                pdf_url = side_panel.find_all('a')[0]['href'][2:]
                detail_area = soup.find("div", {"id": "accMetadata"}).find_all("div", {"class":"row"})
            except NoSuchElementException:
                return []

        date = ""
        full_title = ""
        bill_num = ""
        bill_type = ""
        congress = ""
        bill_version = ""
        sponsor = ""

        for item in detail_area:
            span = item.find('span')
            if span:
                if "Last Action Date Listed" in span.text:
                    date = item.find('p').text
                elif "Full Title" in span.text:
                    full_title = item.find('p').text
                elif "Bill Number" in span.text:
                    bill_num = item.find('p').text.split()[-1]
                    bill_type = "".join(item.find('p').text.split()[:-1])
                elif "Congress Number" in span.text:
                    congress = item.find('p').text.split()[0]
                elif "Bill Version" in span.text:
                    bill_version = item.find('p').text
                elif "Sponsor" in span.text:
                    sponsor = item.find('p').text

        doc_title = full_title
        bill_version_short = bill_version[bill_version.find("(")+1:bill_version.find(")")]
        doc_num = bill_num
        doc_type = bill_type
        doc_name = doc_type + " " + doc_num + " " + bill_version_short + " " + congress
        publication_date = date
        cac_login_required = False
        downloadable_items = []

        pdf_di = DownloadableItem(
            doc_type='pdf',
            web_url= "https://" + pdf_url
            )
        downloadable_items.append(pdf_di)
        version_hash_fields = {
            "pub_date": date,
            "bill_version": bill_version,
            "bill_sponsor": sponsor,
            "congress": congress
        }
        doc = Document(
            doc_name=doc_name.strip(),
            doc_title=doc_title.strip(),
            doc_num=doc_num.strip(),
            doc_type=doc_type.strip(),
            publication_date=publication_date,
            cac_login_required=cac_login_required,
            crawler_used="legislation_pubs",
            source_page_url=driver.current_url,
            version_hash_raw_data=version_hash_fields,
            downloadable_items=downloadable_items
        )

        parsed_docs.append(doc)

        return parsed_docs


class LegislationCrawler(Crawler):
    """Crawler for the example web scraper"""
    def __init__(self, *args, **kwargs):
        super().__init__(
            pager=LegislationPager(
                starting_url=BASE_SOURCE_URL_PAGER,
                specific_congress=kwargs['specific_congress']
            ),
            parser=LegislationParser()
        )


class FakeLegislationCrawler(Crawler):
    """Legislation Publication crawler that just uses stubs and local source files"""
    def __init__(self, *args, **kwargs):
        with open(os.path.join(SOURCE_SAMPLE_DIR, 'army_pubs.html')) as f:
            default_text = f.read()

        super().__init__(
            *args,
            **kwargs,
            pager=LegislationPager(
                requestor=MapBasedPseudoRequestor(
                    default_text=default_text
                ),
                starting_url=BASE_SOURCE_URL_PAGER
            ),
            parser=LegislationParser()
        )
