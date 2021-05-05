# -*- coding: utf-8 -*-
import scrapy
from scrapy import Selector
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver import Chrome
from selenium.common.exceptions import NoSuchElementException
import re
from urllib.parse import urljoin, urlparse
from datetime import datetime

from dataPipelines.gc_scrapy.gc_scrapy.middleware_utils.selenium_request import SeleniumRequest
from dataPipelines.gc_scrapy.gc_scrapy.items import DocItem
from dataPipelines.gc_scrapy.gc_scrapy.GCSeleniumSpider import GCSeleniumSpider

squash_spaces = re.compile(r'\s*[\n\t\r\s+]\s*')
type_pattern_start = re.compile('^[A-Z]+')
type_pattern_mid = re.compile('[A-Z]+')


class AirForcePubsSpider(GCSeleniumSpider):
    name = 'air_force_pubs'
    allowed_domains = ['e-publishing.af.mil']
    start_urls = [
        'https://www.e-publishing.af.mil/Product-Index/#/?view=pubs&orgID=10141&catID=1&series=-1&modID=449&tabID=131/'
    ]

    file_type = "pdf"

    cac_required_options = ['physical.pdf', 'PKI certificate required',
                            'placeholder', 'FOUO', 'for_official_use_only']

    item_count_dropdown_selector = 'label select[name="data_length"]'
    table_selector = "table.epubs-table.dataTable.no-footer.dtr-inline"

    selenium_request_overrides = {
        "wait_until": EC.element_to_be_clickable(
            (By.CSS_SELECTOR, item_count_dropdown_selector))
    }

    def parse(self, response):

        driver: Chrome = response.meta["driver"]
        # change to 100 per page
        Select(
            driver.find_element_by_css_selector(
                self.item_count_dropdown_selector
            )
        ).select_by_value("100")

        anchor_after_current_selector = "div.dataTables_paginate.paging_simple_numbers a.paginate_button.current + a"

        has_next_page = True
        while(has_next_page):
            try:
                el = driver.find_element_by_css_selector(
                    anchor_after_current_selector)

            except NoSuchElementException:
                # expected when on last page, set exit condition then parse table
                has_next_page = False

            try:
                for item in self.parse_table(driver):
                    yield item

            except NoSuchElementException:
                raise NoSuchElementException(
                    f"Failed to find table to scrape from using css selector: {self.table_selector}"
                )

            if has_next_page:
                el.click()
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, self.table_selector)
                    )
                )

    def parse_table(self, driver):
        webpage = Selector(text=driver.page_source)

        row_selector = f'{self.table_selector} tbody tr '

        for row in webpage.css(row_selector):
            product_number_raw = row.css(
                f'td:nth-child(1) a::text').get(default='')
            url_raw = row.css(
                f'td:nth-child(1) a::attr(href)').get(default='')
            title_raw = row.css(
                f'td:nth-child(2) a::text').get(default='')
            publish_date_raw = row.css(
                f'td:nth-child(3) span::text').get(default='')
            certification_date_raw = row.css(
                f'td:nth-child(4) span::text').get(default='')
            last_action_raw = row.css(
                f'td:nth-child(5)::text').get(default='')

            prod_num = squash_spaces.sub(" ", product_number_raw).strip()

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
                doc_type = type_extract[0] if type_extract else type_pattern_start.findall(prod_num)[
                    0]
                doc_num = re.sub(doc_type, '', prod_num_new) if type_extract else re.sub(
                    doc_type, '', prod_num)
                doc_name = ' '.join((doc_type, doc_num))
            else:
                doc_type = type_pattern_start.findall(prod_num)[0]
                # doc_type = 'AF '+doc_type if doc_type in ['HOI', 'QTP'] else doc_type
                doc_num = re.sub(doc_type, '', prod_num)
                doc_name = ' '.join((doc_type, doc_num))

            # DOCUMENT TITLE
            doc_title = squash_spaces.sub(' ', title_raw).strip()

            # PUBLICATION DATE
            pub_date = squash_spaces.sub(' ', publish_date_raw).strip()
            pub_date = pub_date.split(' ')[0]
            pub_date = datetime.strptime(
                pub_date, '%Y%m%d').strftime('%Y-%m-%d')

            # CERTIFICATION DATE
            cert_date = squash_spaces.sub(' ', certification_date_raw).strip()
            cert_date = cert_date.split(' ')[0]
            cert_date = datetime.strptime(
                cert_date, '%Y%m%d').strftime('%Y-%m-%d')

            # LAST DOCUMENT ACTION
            last_action = squash_spaces.sub(' ', last_action_raw).strip()

            # set boolean if CAC is required to view document
            cac_login_required = True if any(x in url_raw for x in self.cac_required_options) \
                or any(x in doc_title for x in self.cac_required_options) \
                or '-S' in prod_num else False

            # all fields that will be used for versioning
            version_hash_fields = {
                # version metadata found on pdf links
                "item_currency": url_raw.split('/')[-1],
                "certified_date": cert_date,
                "last_action": last_action,
                "pub_date": pub_date
            }

            downloadable_items = [
                {
                    "doc_type": self.file_type,
                    "web_url": url_raw,
                    "compression_type": None
                }
            ]

            yield DocItem(
                doc_name=doc_name,
                doc_title=re.sub(r'[^a-zA-Z0-9 ()\\-]', '', doc_title),
                doc_num=doc_num,
                doc_type=doc_type,
                publication_date=pub_date,
                cac_login_required=cac_login_required,
                downloadable_items=downloadable_items,
                version_hash_raw_data=version_hash_fields
            )
