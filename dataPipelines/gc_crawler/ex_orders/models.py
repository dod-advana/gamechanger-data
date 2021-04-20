import bs4
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

from . import SOURCE_SAMPLE_DIR, BASE_SOURCE_URL


class ExOrderPager(Pager):
    """Pager for Executive Order crawler"""

    def iter_page_links(self) -> Iterable[str]:
        """Iterator for page links"""
        yield self.starting_url


class ExOrderParser(Parser):
    """Parser for Executive Order crawler"""

    def parse_docs_from_page(self, page_url: str, page_text: str) -> Iterable[Document]:
        """Parse document objects from page of text"""
        domain = 'http://www.federalregister.gov/'
        soup = bs4.BeautifulSoup(page_text, features="html.parser")
        links = soup.find_all("span", attrs={'class': "links"})
        ex_order_link = links[0].find_all("a")[1]["href"]
        url = abs_url(domain, ex_order_link)

        r = requests.get(url)
        parsed = json.loads(r.text)

        parsed_docs = []
        for execOrder in parsed["results"]:

            # DOWNLOAD INFO
            if execOrder["pdf_url"]:
                pdf_di = DownloadableItem(doc_type='pdf', web_url=execOrder["pdf_url"])
            else:
                pass

            if execOrder["full_text_xml_url"]:
                xml_di = DownloadableItem(
                    doc_type='xml', web_url=execOrder["full_text_xml_url"]
                )
            else:
                pass

            # derive EO Number from context
            if execOrder["executive_order_number"] is None:
                execOrder["executive_order_number"] = str(int(parsed_docs[-1].doc_num) - 1)

            # generate final document object
            doc = Document(
                doc_name="EO " + execOrder["executive_order_number"],
                doc_title=execOrder["title"],
                doc_num=execOrder["executive_order_number"],
                doc_type="EO",
                publication_date=execOrder["publication_date"],
                cac_login_required=False,
                crawler_used="ex_orders",
                source_page_url=execOrder["html_url"],
                version_hash_raw_data={
                    "item_currency": execOrder["publication_date"],
                    "version_hash": execOrder["document_number"],
                    "citation": execOrder["citation"],
                    "title": execOrder["title"],
                },
                access_timestamp="{:%Y-%m-%d %H:%M:%S.%f}".format(
                    datetime.datetime.now()
                ),
                source_fqdn="https://www.federalregister.gov",
                downloadable_items=[pdf_di, xml_di],
            )

            parsed_docs.append(doc)

        return parsed_docs


class ExOrderCrawler(Crawler):
    """Crawler for the example web scraper"""

    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            **kwargs,
            pager=ExOrderPager(starting_url=BASE_SOURCE_URL),
            parser=ExOrderParser(),
        )


class FakeExOrderCrawler(Crawler):
    """Executive Order crawler that just uses stubs and local source files"""

    def __init__(self, *args, **kwargs):
        with open(os.path.join(SOURCE_SAMPLE_DIR, 'ex_orders.html'), encoding='utf-8') as f:
            default_text = f.read()

        super().__init__(
            *args,
            **kwargs,
            pager=ExOrderPager(
                requestor=MapBasedPseudoRequestor(default_text=default_text),
                starting_url=BASE_SOURCE_URL,
            ),
            parser=ExOrderParser(),
        )
