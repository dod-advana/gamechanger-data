import bs4
import re
import os
import requests
import json
import datetime
from typing import Iterable
import itertools
from dataPipelines.gc_crawler.requestors import MapBasedPseudoRequestor
from dataPipelines.gc_crawler.exec_model import Crawler, Parser, Pager
from dataPipelines.gc_crawler.data_model import Document, DownloadableItem
from dataPipelines.gc_crawler.utils import abs_url

from . import SOURCE_SAMPLE_DIR, BASE_SOURCE_URL

def remove_html_tags(text):
    import re
    clean=re.compile('<.*?>')
    return re.sub(clean,'',text)

class ArmyReservePager(Pager):
    """Pager for ArmyReserve Issuance crawler"""

    def iter_page_links(self) -> Iterable[str]:
        """Iterator for page links"""
        url = 'https://www.usar.army.mil/Publications/'

        yield url


class ArmyReserveParser(Parser):
    """Parser for ArmyReserve Issuance crawler"""

    def parse_docs_from_page(self, page_url: str, page_text: str) -> Iterable[Document]:
        """Parse document objects from page of text"""

        # parse html response
        page2 = requests.get(page_url)
        soup2 = bs4.BeautifulSoup(page2.content, 'html.parser')
        doc_num = []
        pdf = []
        doc_title = []
        datelist = []
        doctype = []
        parsed_docs = []
        webpart2 = soup2.find("div", {"class": "skin-pane2 col-md-8"})
        meta = webpart2.find_all("div")
        for row in meta:
            if ((remove_html_tags((str(row))).isspace()) or not remove_html_tags((str(row)))):
                continue
            for cell in row.find_all('p'):
                # print(cell.find("strong"))
                words = ''
                links = cell.find_all("a")
                link_list = list(links)
                # print(links)
                nums = []
                pdf_links = [link['href'] for link in link_list if "pdf" in link['href'] or "aspx" in link['href']]
                if not pdf_links:
                    continue
                pdf.append(str(pdf_links[0]))
                # print(pdf_links)
                words = remove_html_tags((str(cell.find("strong")))).encode('ascii', 'ignore').decode('ascii').lstrip(
                    " ").rstrip(" ")
                words = " ".join(words.split())
                # print(words)
                # else:
                # print(cell)
                doc_num.append(words)
                pdf.append(str(pdf_links[0]))
                title = [text for text in cell.find_all(text=True) if text.parent.name != "strong"]
                doc_title.append(title)
        pub_links = []
        [pub_links.append(x) for x in pdf if x not in pub_links]
        document_name = []
        [document_name.append(x) for x in doc_num if x not in document_name]
        document_type = []
        [document_type.append(' '.join(x.split()[0:2])) for x in document_name]
        document_number = []
        [document_number.append(' '.join(x.split()[2:])) for x in document_name]
        document_title = []
        [document_title.append(x) for x in doc_title if x not in document_title]
        document_title = [item for sublist in document_title for item in sublist]
        document_title = [str(item).encode('ascii', 'ignore').decode('ascii').lstrip(" ").rstrip(" ") for item in
                          document_title]
        final = list(itertools.zip_longest(document_type, document_number, document_title, pub_links))
        final = [list(x) for x in final]
        for item in final:
            doc_name = item[0]+' '+item[1]
            if (item[2] is None):
                doc_title=""
            else:
                doc_title = item[2]
            doc_num = item[1]
            doc_type = item[0]
            publication_date = "N/A"
            if item[3].startswith("https"):
                cac_login_required=True
                url = item[3]
                url = url.replace(" ","%20")
            else:
                cac_login_required=False
                url = "https://www.usar.army.mil"+item[3]
                url = url.replace(" ","%20")
            pdf_di = DownloadableItem(doc_type='pdf', web_url=url)
            version_hash_fields = {
                "item_currency": str(url).split('/')[-1],  # version metadata found on pdf links
                "document_title": doc_title.strip(),
                "document_number": doc_num.strip()
            }
            if (str(doc_type).startswith("USAR") == False):
                doc_title = doc_name
                doc_num = ""
                doc_type = "USAR Doc"
                version_hash_fields = {
                    "item_currency": str(url).split('/')[-1],  # version metadata found on pdf links
                    "document_title": doc_title.strip(),
                    "document_number": doc_num.strip()}

            doc = Document(
                doc_name=doc_name.strip(),
                doc_title=re.sub('\\"', '', doc_title),
                doc_num=doc_num.strip(),
                doc_type=doc_type.strip(),
                publication_date=publication_date,
                cac_login_required=cac_login_required,
                crawler_used="Army_Reserve",
                source_page_url=page_url.strip(),
                version_hash_raw_data=version_hash_fields,
                downloadable_items=[pdf_di]
            )

            parsed_docs.append(doc)
        return parsed_docs


class ArmyReserveCrawler(Crawler):
    """Crawler for the example web scraper"""
    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            **kwargs,
            pager=ArmyReservePager(
                starting_url=BASE_SOURCE_URL
            ),
            parser=ArmyReserveParser()
        )


class FakeArmyReserveCrawler(Crawler):
    """Army Reserve crawler that just uses stubs and local source files"""
    def __init__(self, *args, **kwargs):
        with open(os.path.join(SOURCE_SAMPLE_DIR, 'ArmyReserve.html')) as f:
            default_text = f.read()

        super().__init__(
            *args,
            **kwargs,
            pager=ArmyReservePager(
                requestor=MapBasedPseudoRequestor(
                    default_text=default_text
                ),
                starting_url=BASE_SOURCE_URL
            ),
            parser=ArmyReserveParser()
        )
