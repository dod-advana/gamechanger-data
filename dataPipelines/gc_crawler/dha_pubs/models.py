from bs4 import BeautifulSoup
import re
import os
import requests
import json
import datetime
from typing import Iterable
import sys
from dataPipelines.gc_crawler.requestors import MapBasedPseudoRequestor
from dataPipelines.gc_crawler.exec_model import Crawler, Parser, Pager
from dataPipelines.gc_crawler.data_model import Document, DownloadableItem
from dataPipelines.gc_crawler.utils import abs_url

from . import SOURCE_SAMPLE_DIR, BASE_SOURCE_URL
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class DHAPager(Pager):
    """Pager for DoD Issuance crawler"""

    def iter_page_links(self) -> Iterable[str]:
        """Iterator for page links"""
        base_url = 'https://health.mil/About-MHS/OASDHA/Defense-Health-Agency/Resources-and-Management/DHA-Publications'
        yield base_url


class DHAParser(Parser):
    """
    Parser for DHA crawler
    """

    def parse_docs_from_page(self, page_url: str, page_text: str) -> Iterable[Document]:
        """Parse document objects from page of text"""
        # get the data
        data = requests.get(page_url)

        # load data into bs4
        soup = BeautifulSoup(data.text, 'html.parser')
        # links = []
        pdf_dis = []
        dates = []
        table = []
        version_hash_fields = []

        for tr in soup.find_all('tr'):
            date_col = soup.find_all('td', attrs={'class': 'fd-col2'})
            hyperlink_col = soup.find_all('td', attrs={'class': 'fd-col1'})
            values = [td.text for td in tr.find_all('td')]
            table.append(values)
            for link in hyperlink_col:
                pdf_url = 'https://www.health.mil/' + link.find('a')['href']
                pdf_di = DownloadableItem(doc_type='pdf',
                                          web_url=pdf_url)
                pdf_dis.append(pdf_di)
            for date in date_col:
                dates.append(date.text)

        doc_nums = []
        doc_titles = []
        doc_names = []
        for row in table[1:]:
            doc_data = row[0].split(':')

            if len(doc_data) == 1:  # if no colon then no doc number
                if doc_data[0] == "(DTM)-19-004 -Military Service by Transgender Persons and Persons with Gender Dysphoria (Change 1)":
                    doc_nums.append("19-004")
                    doc_names.append("DTM")
                    doc_titles.append(doc_data[0][14:])
                    version_hash_fields.append({"doc_name": 'DTM', "doc_title": doc_data[0][14:]})
                else:
                    doc_nums.append(" ")
                    doc_titles.append(doc_data[0])
                    doc_names.append(doc_data[0])
                    version_hash_fields.append({"doc_name": doc_data[0], "doc_title": doc_data[0]})
            else:

                tmptitle = doc_data[1][1:].replace("\u201cClinical","Clinical").replace("System,\u201d","System").replace("BUILDER\u2122 ", "Builder").replace("\u2013","")

                if "Volume" in tmptitle:
                    doc_nums.append(doc_data[0][7:]+" Volume "+tmptitle.split()[-1])
                else:
                    doc_nums.append(doc_data[0][7:])
                doc_titles.append(doc_data[1][1:].replace("\u201cClinical","Clinical").replace("System,\u201d","System").replace("BUILDER\u2122 ", "Builder").replace("\u2013",""))
                doc_names.append(doc_data[0][:6])

                version_hash_fields.append({"doc_name": doc_data[0][:7], "doc_title": doc_data[1]})

        parsed_docs = []
        page_url = 'https://www.health.mil/About-MHS/OASDHA/Defense-Health-Agency/Resources-and-Management/DHA-Publications'
        num_docs = len(doc_nums)
        for i in range(num_docs):
            # put all the relevant info into dictionaries
            doc = Document(doc_type=doc_names[i].replace(" ","-"),
                           doc_title=doc_titles[i],
                           doc_num=doc_nums[i],
                           doc_name=doc_names[i].replace(" ","-")+" "+doc_nums[i],
                           publication_date=dates[i],
                           cac_login_required=False,
                           crawler_used='dha_pubs',
                           source_page_url=page_url,
                           downloadable_items=[pdf_dis[i]],
                           version_hash_raw_data=version_hash_fields[i])
            parsed_docs.append(doc)

        return parsed_docs


class DHACrawler(Crawler):
    """Crawler for the example web scraper"""

    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            **kwargs,
            pager=DHAPager(
                starting_url=BASE_SOURCE_URL
            ),
            parser=DHAParser()
        )


class FakeDHACrawler(Crawler):
    """DoD Issuance crawler that just uses stubs and local source files"""

    def __init__(self, *args, **kwargs):
        with open(os.path.join(SOURCE_SAMPLE_DIR, 'Defense Health Agency Publications _ Health.mil.html')) as f:
            default_text = f.read()

        super().__init__(
            *args,
            **kwargs,
            pager=DHAPager(
                requestor=MapBasedPseudoRequestor(
                    default_text=default_text
                ),
                starting_url=BASE_SOURCE_URL
            ),
            parser=DHAParser()
        )
