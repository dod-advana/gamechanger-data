# -*- coding: utf-8 -*-
import scrapy
from scrapy import Selector
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver import Chrome
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from itertools import zip_longest
import re

from dataPipelines.gc_scrapy.gc_scrapy.items import DocItem
from dataPipelines.gc_scrapy.gc_scrapy.GCSeleniumSpider import GCSeleniumSpider

from time import sleep


class NavyReserveSpider(GCSeleniumSpider):
    name = "navy_reserves"
    allowed_domains = ['navyreserve.navy.mil']
    start_urls = [
        'https://www.navyreserve.navy.mil/'
    ]

    file_type = 'pdf'
    cac_login_required = False

    tables_selector = 'table.dnnGrid'

    def parse(self, response):
        driver: Chrome = response.meta["driver"]
        pages = [
            'https://www.navyreserve.navy.mil/Resources/Official-Guidance/Instructions/',
            'https://www.navyreserve.navy.mil/Resources/Official-Guidance/RESPERSMAN/',
            'https://www.navyreserve.navy.mil/Resources/Official-Guidance/Notices/'
        ]

        for page_url in pages:
            for item in self.parse_page(page_url, driver):
                yield item

    def parse_page(self, url, driver) -> DocItem:
        if "Instruction" in url or "Notice" in url:
            type_prefix = "COMNAVRESFORCOM"
        if "RESPERSMAN" in url:
            type_prefix = "RESPERSMAN"

        driver.get(url)
        init_webpage = Selector(text=driver.page_source)
        # get a list headers from tables that need parsing
        table_headers_raw = init_webpage.css(
            'div.base-container.blue-header2 h2.title span.Head::text').getall()

        # associate a table header with a table index
        for table_index, header_text_raw in enumerate(table_headers_raw):

            doc_type = header_text_raw.strip()

            has_next_page = True
            while has_next_page:
                # have to reselect page source each loop b/c it refreshes on page change
                webpage = Selector(text=driver.page_source)

                # grab associated tables again each page
                data_table = webpage.css(self.tables_selector)[table_index]
                paging_table = driver.find_elements_by_css_selector('table.PagingTable')[
                    table_index]

                # check has next page link
                try:
                    el = paging_table.find_element_by_xpath(
                        "//a[contains(text(), 'Next')]")
                except (StaleElementReferenceException, NoSuchElementException):
                    # expected when one page or on last page, set exit condition then parse table
                    has_next_page = False
                except Exception as e:
                    # other exceptions not expected, dont page this table and try to continue
                    print(
                        f'Unexpected Exception - attempting to continue: {e}')
                    has_next_page = False

                # parse data table
                try:
                    for tr in data_table.css('tbody tr:not(.dnnGridHeader)'):
                        doc_num_raw = tr.css('td:nth-child(1)::text').get()
                        doc_title_raw = tr.css('td:nth-child(2)::text').get()
                        href_raw = tr.css(
                            'td:nth-child(3) a::attr(href)').get()

                        doc_num = doc_num_raw.strip().replace(" ", "_").replace(u'\u200b', '')
                        if not bool(re.search(r'\d', doc_num)):
                            continue
                        if "RESPERSMAN" in driver.current_url:
                            type_suffix = ""
                        elif '.' in doc_num:
                            type_suffix = "INST"
                        else:
                            type_suffix = "NOTE"

                        doc_title = doc_title_raw.strip()

                        doc_type = type_prefix + type_suffix
                        doc_name = doc_type + " " + doc_num
                        if re.search(r'\(\d\)', doc_title):
                            doc_name_suffix = re.split('\(', doc_title)
                            doc_name_suffix = re.split(
                                '\)', doc_name_suffix[1])
                            if doc_name_suffix[0].strip() != "":
                                doc_name = doc_name + '_' + doc_name_suffix[0]
                            if len(doc_name_suffix) > 1 and doc_name_suffix[1].strip() != "":
                                doc_name = doc_name + '_' + \
                                    doc_name_suffix[1].strip().replace(
                                        " ", "_")

                        web_url = self.ensure_full_href_url(
                            href_raw, driver.current_url)

                        doc_title = self.ascii_clean(doc_title_raw)

                        version_hash_fields = {
                            "item_currency": href_raw,
                            "document_title": doc_title,
                            "document_number": doc_num
                        }

                        downloadable_items = [
                            {
                                "doc_type": self.file_type,
                                "web_url": web_url.replace(' ', '%20'),
                                "compression_type": None
                            }
                        ]

                        yield DocItem(
                            doc_name=doc_name.strip(),
                            doc_title=doc_title.strip(),
                            doc_num=doc_num.strip(),
                            doc_type=doc_type.strip(),
                            downloadable_items=downloadable_items,
                            version_hash_raw_data=version_hash_fields,
                            source_page_url=driver.current_url
                        )
                except:
                    print(
                        f'Unexpected Parsing Exception - attempting to continue: {e}')
                    pass

                if has_next_page:
                    el.click()
                    # wait until paging table is stale from page load
                    WebDriverWait(driver, 5).until(
                        EC.staleness_of(paging_table))
