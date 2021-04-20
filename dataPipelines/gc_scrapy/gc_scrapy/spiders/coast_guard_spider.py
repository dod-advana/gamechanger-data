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
from time import sleep


class CoastGuardSpider(GCSeleniumSpider):
    name = 'Coast_Guard'
    allowed_domains = ['dcms.uscg.mil']
    start_urls = [
        'https://www.dcms.uscg.mil/Our-Organization/Assistant-Commandant-for-C4IT-CG-6/The-Office-of-Information-Management-CG-61/About-CG-Directives-System/Commandant-Instruction-Manuals/smdpage2823/1/'
    ]
    doc_type = 'CIM'
    file_type = "pdf"

    cac_login_required = False
    current_page_selector = 'div.numericDiv ul li.active a.Page'
    next_page_selector = 'div.numericDiv ul li.active + li a'
    rows_selector = "table.Dashboard tbody tr"

    selenium_request_overrides = {
        "wait_until": EC.element_to_be_clickable(
            (By.CSS_SELECTOR, current_page_selector))
    }

    @staticmethod
    def clean(text):
        return text.encode('ascii', 'ignore').decode('ascii').strip()

    @staticmethod
    def get_file_type(url):
        file_url, _, _ = url.partition('?')
        _, _, extension = file_url.rpartition('.')
        return extension.lower()

    def parse(self, response):

        driver: Chrome = response.meta["driver"]

        has_next_page = True
        while(has_next_page):
            try:
                el = driver.find_element_by_css_selector(
                    self.next_page_selector)

            except NoSuchElementException:
                # expected when on last page, set exit condition then parse table
                has_next_page = False

            for item in self.parse_table(driver):
                yield item

            if has_next_page:
                el.click()
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, self.rows_selector)
                    )
                )

    def parse_table(self, driver):
        webpage = Selector(text=driver.page_source)

        for row in webpage.css(self.rows_selector):
            doc_num_raw = row.css('td:nth-child(1)::text').get()
            doc_num = doc_num_raw.replace('CIM_', '').replace('_', '.')

            doc_title_raw = row.css('td:nth-child(2) a::text').get()
            doc_title = self.clean(doc_title_raw)
            href_raw = row.css('td:nth-child(2) a::attr(href)').get()

            if href_raw.startswith('/'):
                web_url = urljoin(driver.current_url, href_raw)
            else:
                web_url = href_raw

            publication_date = row.css('td:nth-child(5)::text').get()

            # all fields that will be used for versioning
            version_hash_fields = {
                "item_currency": href_raw.replace(' ', '%20'),
                "document_title": doc_title,
                "document_number": doc_num
            }

            file_type = self.get_file_type(web_url)

            downloadable_items = [
                {
                    "doc_type": file_type,
                    "web_url": web_url.replace(' ', '%20'),
                    "compression_type": None
                }
            ]

            yield DocItem(
                doc_name=f"{self.doc_type} {doc_num}",
                doc_title=doc_title,
                doc_num=doc_num,
                # doc_type=doc_type,
                publication_date=publication_date,
                # cac_login_required=cac_login_required,
                downloadable_items=downloadable_items,
                version_hash_raw_data=version_hash_fields,
                source_page_url=driver.current_url
            )
