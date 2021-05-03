from bs4 import BeautifulSoup
import re
import os
import requests
import json
import datetime
from typing import Iterable
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from dataPipelines.gc_crawler.requestors import MapBasedPseudoRequestor
from dataPipelines.gc_crawler.exec_model import Crawler, Parser, Pager
from dataPipelines.gc_crawler.data_model import Document, DownloadableItem
from dataPipelines.gc_crawler.utils import abs_url

from . import SOURCE_SAMPLE_DIR, BASE_SOURCE_URL


class DFarSubpartPager(Pager):
    """Pager for DoD Issuance crawler"""

    def iter_page_links(self) -> Iterable[str]:
        """Iterator for page links"""
        base_url = 'https://www.acquisition.gov/dfars'
        yield base_url


class DFarSubpartParser(Parser):
    """Parser for DoD Issuance crawler"""

    def parse_docs_from_page(self, page_url: str, page_text: str) -> Iterable[Document]:
        """Parse document objects from page of text"""

        # parse html response
        base_url = 'https://www.acquisition.gov/dfars'
        soup = BeautifulSoup(requests.get(base_url).text, 'html.parser')

        # publication date of subparts will depend on the effective pub of DFAR
        def get_date():
            effective_pub_table = soup.find(lambda tag: tag.name == 'table' and tag.has_attr('id') and tag['id'] == "browse-table-full")
            pub_date = ''
            for r in effective_pub_table.find_all('tr')[1:]:
                pub_date = r.find_all('td')[1].text.strip()
            return pub_date

        # now scrape all subparts for DFAR
        table = soup.find(
            lambda tag: tag.name == 'table' and tag.has_attr('id') and tag['id'] == "browse-table")
        count = 0
        parsed_docs = []
        for row in table.find_all('tr')[1:]:
            # clear all to ensure no rollover
            doc_num = ''
            doc_name = ''
            doc_title = ''

            cac_login_required = False
            pdf_url = ''
            pdf_di = None
            doc_type = ''
            if count > 0:
                doc_title = row.find_all('td')[0].text.strip().replace('\u2014',' ').replace('\u2013 ', ' ')

                if doc_title[0:8].lower() == 'appendix':
                    break
                doc_num = doc_title.split()[0] + ' ' + doc_title.split()[1]
                pdf_url = 'https://www.acquisition.gov' + row.find_all('td')[3].find('a')['src']
                pdf_di = DownloadableItem(
                    doc_type='html',
                    web_url=pdf_url
                )

                version_hash_fields = {
                    "item_currency": pdf_url.split('/')[-1],  # version metadata found on pdf links
                    "pub_date": get_date().strip()
                }
                doc_type = 'DFARS'
                doc = Document(
                    doc_name=doc_type + " " + doc_num,
                    doc_title=doc_title,
                    doc_num=doc_num,
                    doc_type=doc_type,
                    publication_date=get_date(),
                    cac_login_required=cac_login_required,
                    crawler_used="dfar_subpart_regs",
                    source_page_url=page_url.strip(),
                    version_hash_raw_data=version_hash_fields,
                    downloadable_items=[pdf_di]
                )
                parsed_docs.append(doc)
            count+=1
        return parsed_docs

class DFarSubpartCrawler(Crawler):
    """Crawler for the example web scraper"""
    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            **kwargs,
            pager=DFarSubpartPager(
                starting_url=BASE_SOURCE_URL
            ),
            parser=DFarSubpartParser()
        )

