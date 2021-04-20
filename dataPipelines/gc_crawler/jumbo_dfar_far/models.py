from bs4 import BeautifulSoup
import re
import os
import requests
import json
import datetime
from typing import Iterable

from dataPipelines.gc_crawler.requestors import MapBasedPseudoRequestor
from dataPipelines.gc_crawler.exec_model import Crawler, Parser, Pager
from dataPipelines.gc_crawler.data_model import Document, DownloadableItem
from dataPipelines.gc_crawler.utils import abs_url
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from . import SOURCE_SAMPLE_DIR, BASE_SOURCE_URL


class JumboFarDFarPager(Pager):
    """Pager for DoD Issuance crawler"""

    def iter_page_links(self) -> Iterable[str]:
        """Iterator for page links"""
        base_url = 'https://www.acquisition.gov/'
        yield base_url


class JumboFarDFarParser(Parser):
    """Parser for DoD Issuance crawler"""

    def parse_docs_from_page(self, page_url: str, page_text: str) -> Iterable[Document]:
        """Parse document objects from page of text"""

        # parse html response
        base_url = 'https://www.acquisition.gov/'

        far_url = base_url + 'far'
        dfar_url = base_url + 'dfars'
        sources = [far_url, dfar_url]
        parsed_docs = []

        for data in sources:
            # reset variables to ensure there is no carryover between rows
            doc_num = ''
            doc_name = ''
            doc_title = ''
            publication_date = ''
            cac_login_required = False
            pdf_url = ''
            pdf_di = None
            doc_type = ''
            soup = BeautifulSoup(requests.get(data).text, 'html.parser')
            table = soup.find(
                lambda tag: tag.name == 'table' and tag.has_attr('id') and tag['id'] == "browse-table-full")

            if data == far_url:
                for row in table.find_all('tr')[1:]:
                    doc_title = 'Federal Acquisition Regulation'
                    doc_num = row.find_all('td')[0].text.strip()
                    publication_date = row.find_all('td')[1].text.strip()
                    pdf_url = base_url + row.find_all('td')[4].find('a')['href']
                    pdf_di = DownloadableItem(
                        doc_type='pdf',
                        web_url=pdf_url
                    )
                    doc_type = "FAR"
                    doc_name = doc_type + ' ' + doc_num
            if data == dfar_url:
                for row in table.find_all('tr')[1:]:
                    doc_title = 'Defense Federal Acquisition Regulation'
                    doc_num = row.find_all('td')[0].text.split()
                    doc_num = doc_num[2].replace("/", "-")
                    publication_date = row.find_all('td')[1].text.strip()
                    pdf_url = base_url + row.find_all('td')[5].find('a')['href']
                    pdf_di = DownloadableItem(
                        doc_type='pdf',
                        web_url=pdf_url
                    )
                    doc_type = "DFAR"
                    doc_name = doc_type + ' ' + doc_num

            version_hash_fields = {
                "item_currency": pdf_url.split('/')[-1],  # version metadata found on pdf links
                "pub_date": publication_date.strip()
            }

            doc = Document(
                doc_name=doc_name,
                doc_title=doc_title,
                doc_num=doc_num,
                doc_type=doc_type,
                publication_date=publication_date,
                cac_login_required=cac_login_required,
                crawler_used="jumbo_" + doc_type,
                source_page_url=page_url.strip(),
                version_hash_raw_data=version_hash_fields,
                downloadable_items=[pdf_di]
            )

            parsed_docs.append(doc)

        return parsed_docs


class JumboFarDFarCrawler(Crawler):
    """Crawler for the example web scraper"""
    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            **kwargs,
            pager=JumboFarDFarPager(
                starting_url=BASE_SOURCE_URL
            ),
            parser=JumboFarDFarParser()
        )


class FakeJumboFarDFarCrawler(Crawler):
    """DoD Issuance crawler that just uses stubs and local source files"""
    def __init__(self, *args, **kwargs):
        with open(os.path.join(SOURCE_SAMPLE_DIR, 'https://www.acquisition.gov/')) as f:
            default_text = f.read()

        super().__init__(
            *args,
            **kwargs,
            pager=JumboFarDFarPager(
                requestor=MapBasedPseudoRequestor(
                    default_text=default_text
                ),
                starting_url=BASE_SOURCE_URL
            ),
            parser=JumboFarDFarParser()
        )
