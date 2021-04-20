import bs4
import re
import os
import time
from datetime import datetime
from typing import Iterable, Tuple
from selenium.webdriver.support.ui import WebDriverWait  # for implicit and explict waits
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains

from dataPipelines.gc_crawler.requestors import MapBasedPseudoRequestor
from dataPipelines.gc_crawler.exec_model import Crawler, Parser, Pager
from dataPipelines.gc_crawler.data_model import Document, DownloadableItem
from dataPipelines.gc_crawler.utils import abs_url

from . import SOURCE_SAMPLE_DIR, BASE_SOURCE_URL, driver


class AFPager(Pager):
    """Pager for Air Force crawler"""

    def iter_page_links(self) -> Iterable[str]:
        """Iterator for page links"""
        pass

    def iter_page_links_with_text(self) -> Iterable[Tuple[str, str]]:

        # use the webdriver to get url
        driver.get(self.starting_url)

        # select maximum documents per page
        WebDriverWait(driver, 5).until(
            ec.element_to_be_clickable((By.XPATH, '//*[@id="data_length"]/label/select/option[4]'))).click()

        # extract the last page number
        last_page_button = WebDriverWait(driver, 5).until(
            ec.element_to_be_clickable((By.XPATH, '//*[@id="data_paginate"]/span/span/following-sibling::a')))
        last_page = int(last_page_button.text.strip())

        # init page tracker
        next_page_num = 1

        # loop through pages until the last
        while next_page_num <= last_page:

            if next_page_num != 1:
                # extract the next link
                next_page = WebDriverWait(driver, 5).until(
                    ec.element_to_be_clickable((By.XPATH, '//*[@class="paginate_button current"]/following-sibling::a')))
                ActionChains(driver).move_to_element(next_page).perform()
                next_page.click()

            # increase next page tracker
            next_page_num += 1

            html_list = []
            html = driver.execute_script('return document.documentElement.outerHTML')
            html_list.append((driver.current_url, html))
            yield html_list[-1]


class AFParser(Parser):
    """Parser for Air Force crawler"""

    def parse_docs_from_page(self, page_url: str, page_text: str) -> Iterable[Document]:
        """Parse document objects from page of text"""

        # parse html response
        base_url = 'https://www.e-publishing.af.mil/'
        soup = bs4.BeautifulSoup(page_text, features='html.parser')
        table = soup.find('table', attrs={'class': 'epubs-table dataTable no-footer dtr-inline'})
        rows = table.find_all('tr')

        # iterate through each row of the table
        parsed_docs = []
        cac_required = ['physical.pdf', 'PKI certificate required', 'placeholder', 'FOUO', 'for_official_use_only']

        for row in rows[1:]:

            # extract data from cell
            cells = row.find_all('td')

            # extract pdf link
            pdf_url = abs_url(base_url, cells[0].a['href']).replace(' ', '%20')
            pdf_di = DownloadableItem(
                doc_type='pdf',
                web_url=pdf_url
            )

            # extract product number
            squash_spaces = re.compile(r'\s*[\n\t\r\s+]\s*')
            prod_num = squash_spaces.sub(" ", cells[0].text).strip()

            # DOCUMENT NAME, NUMBER & TYPE
            # set patterns for document type
            type_pattern_start = re.compile('^[A-Z]+')
            type_pattern_mid = re.compile('[A-Z]+')

            # handle special cases
            if prod_num.find('CFETP') != -1:
                doc_type = 'CFETP'
                doc_num = re.sub(doc_type, '', prod_num)
                doc_name = ' '.join((doc_type, doc_num))
            elif prod_num == '2T0X1_F-35_AFJQS':
                doc_type = 'AFJQS'
                doc_num = '2T0X1_F-35'
                doc_name = ' '.join((doc_type, doc_num))
            elif prod_num == 'AFHandbook1':
                doc_type = 'AFH'
                doc_num = '1'
                doc_name = ' '.join((doc_type, doc_num))
            elif prod_num == 'BOWFUSF':
                doc_type = 'AF MISC'
                doc_name = 'BOWFUSF'
            elif prod_num == 'MCMUS':
                doc_type = 'AF MISC'
                doc_name = 'MCMUS'
            elif prod_num.endswith('SMALL'):
                prod_num_new = re.sub('SMALL', '', prod_num)
                doc_type = type_pattern_start.findall(prod_num_new)[0]
                doc_num = re.sub(doc_type, '', prod_num_new)
                doc_name = ' '.join((doc_type, doc_num))
            elif 'DOD' in prod_num.upper() or 'DESR' in prod_num.upper():
                prod_num_new = prod_num.split('.')[-1]
                prod_num_new = prod_num_new.split('_')[-1]
                type_extract = type_pattern_mid.findall(prod_num_new)
                doc_type = type_extract[0] if type_extract else type_pattern_start.findall(prod_num)[0]
                doc_num = re.sub(doc_type, '', prod_num_new) if type_extract else re.sub(doc_type, '', prod_num)
                doc_name = ' '.join((doc_type, doc_num))
            else:
                doc_type = type_pattern_start.findall(prod_num)[0]
                # doc_type = 'AF '+doc_type if doc_type in ['HOI', 'QTP'] else doc_type
                doc_num = re.sub(doc_type, '', prod_num)
                doc_name = ' '.join((doc_type, doc_num))

            # DOCUMENT TITLE
            doc_title = squash_spaces.sub(' ', cells[1].text).strip()

            # PUBLICATION DATE
            pub_date = squash_spaces.sub(' ', cells[2].text).strip()
            pub_date = pub_date.split(' ')[0]
            pub_date = datetime.strptime(pub_date, '%Y%m%d').strftime('%Y-%m-%d')

            # CERTIFICATION DATE
            cert_date = squash_spaces.sub(' ', cells[3].text).strip()
            cert_date = cert_date.split(' ')[0]
            cert_date = datetime.strptime(cert_date, '%Y%m%d').strftime('%Y-%m-%d')

            # LAST DOCUMENT ACTION
            last_action = squash_spaces.sub(' ', cells[4].text).strip()

            # set boolean if CAC is required to view document
            cac_login_required = True if any(x in pdf_url for x in cac_required) \
                                         or any(x in doc_title for x in cac_required) \
                                         or '-S' in prod_num else False

            # all fields that will be used for versioning
            version_hash_fields = {
                "item_currency": pdf_url.split('/')[-1],  # version metadata found on pdf links
                "certified_date": cert_date,
                "last_action": last_action,
                "pub_date": pub_date
            }

            doc = Document(
                doc_name=doc_name,
                doc_title=re.sub(r'[^a-zA-Z0-9 ()\\-]', '', doc_title),
                doc_num=doc_num,
                doc_type=doc_type,
                publication_date=pub_date,
                cac_login_required=cac_login_required,
                source_page_url=page_url.strip(),
                version_hash_raw_data=version_hash_fields,
                downloadable_items=[pdf_di],
                crawler_used='air_force_pubs'
            )

            parsed_docs.append(doc)

        # slow down requests so we don't get banned
        time.sleep(5)

        return parsed_docs


class AFCrawler(Crawler):
    """Crawler for the example web scraper"""
    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            **kwargs,
            pager=AFPager(
                starting_url=BASE_SOURCE_URL
            ),
            parser=AFParser()
        )


class FakeAFCrawler(Crawler):
    """Air Force crawler that just uses stubs and local source files"""
    def __init__(self, *args, **kwargs):
        with open(os.path.join(SOURCE_SAMPLE_DIR, 'air_force_pubs.html')) as f:
            default_text = f.read()

        super().__init__(
            *args,
            **kwargs,
            pager=AFPager(
                requestor=MapBasedPseudoRequestor(
                    default_text=default_text
                ),
                starting_url=BASE_SOURCE_URL
            ),
            parser=AFParser()
        )
