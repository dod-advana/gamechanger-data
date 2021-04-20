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

class OPMPager(Pager):
    """Pager for OPM crawler"""

    def iter_page_links(self) -> Iterable[str]:
        yield BASE_SOURCE_URL


class OPMParser(Parser):
    """Parser for OPM crawler"""

    def parse_docs_from_page(self, page_url: str, page_text: str) -> Iterable[Document]:
        """Parse document objects from page of text"""

        base_url = 'https://www.whitehouse.gov'

        r = requests.get(BASE_SOURCE_URL)
        soup = bs4.BeautifulSoup(r.content, features="html.parser")

        parsed_nums = []

        # get target column of list items
        parsed_docs = []
        li_list = soup.find_all('li')
        for li in li_list:
            doc_type = 'OMBM'
            doc_num = ''
            doc_name = ''
            doc_title = ''
            chapter_date = ''
            publication_date = ''
            cac_login_required = False
            pdf_url = ''
            exp_date = ''
            issuance_num = ''
            pdf_di = None
            if 'supersede' not in li.text.lower():
                a_list = li.findChildren('a')
                for a in a_list:
                    link = a.get('href', None) or a.get('data-copy-href', None)
                    if link.lower().endswith('.pdf'):
                        if link.startswith('http'):
                            pdf_url = link
                        else:
                            pdf_url = base_url + link.strip()
                    commaTokens = a.text.strip().split(',', 1)
                    spaceTokens = a.text.strip().split(' ', 1)
                    if len(commaTokens) > 1 and len(commaTokens[0]) < len(spaceTokens[0]):
                        doc_num=commaTokens[0]
                        doc_title=re.sub(r'^.*?,', '', a.text.strip())
                        doc_name="OMBM " + doc_num
                    elif len(spaceTokens) > 1 and len(spaceTokens[0]) < len(commaTokens[0]):
                        doc_num=spaceTokens[0].rstrip(',.*')
                        doc_title=spaceTokens[1]
                        doc_name="OMBM " + doc_num
                    possible_date=li.text[li.text.find("(")+1:li.text.find(")")]
                    if re.match(pattern=r".*, \d{4}.*", string=possible_date):
                        publication_date=possible_date
                if pdf_url != '' and doc_num.count('-') == 2:
                    pdf_di = DownloadableItem(
                        doc_type='pdf',
                        web_url=pdf_url
                    )
                    version_hash_fields = {
                        "item_currency": pdf_url.split('/')[-1],  # version metadata found on pdf links
                        "pub_date": publication_date.strip(),
                    }
                    parsed_title=re.sub('\\"', '', doc_title)
                    parsed_num=doc_num.strip()
                    if parsed_num not in parsed_nums:
                        doc = Document(
                            doc_name=doc_name.strip(),
                            doc_title=parsed_title,
                            doc_num=parsed_num,
                            doc_type=doc_type.strip(),
                            publication_date=publication_date,
                            cac_login_required=cac_login_required,
                            crawler_used="opm_pubs",
                            source_page_url=BASE_SOURCE_URL.strip(),
                            version_hash_raw_data=version_hash_fields,
                            downloadable_items=[pdf_di]
                        )
                        parsed_docs.append(doc)
                        parsed_nums.append(parsed_num)
        return parsed_docs


class OPMCrawler(Crawler):
    """Crawler for the example web scraper"""

    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            **kwargs,
            pager=OPMPager(
                starting_url=BASE_SOURCE_URL
            ),
            parser=OPMParser()
        )


class FakeOPMCrawler(Crawler):
    """OPM crawler that just uses stubs and local source files"""

    def __init__(self, *args, **kwargs):
        with open(os.path.join(SOURCE_SAMPLE_DIR, 'dod_issuances.html')) as f:
            default_text = f.read()

        super().__init__(
            *args,
            **kwargs,
            pager=OPMPager(
                requestor=MapBasedPseudoRequestor(
                    default_text=default_text
                ),
                starting_url=BASE_SOURCE_URL
            ),
            parser=OPMParser()
        )
