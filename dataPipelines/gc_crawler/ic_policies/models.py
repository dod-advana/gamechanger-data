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


class ICPager(Pager):
    """Pager for Intelligence Community crawler"""

    def iter_page_links(self) -> Iterable[str]:
        """Iterator for page links"""
        base_url = 'https://www.dni.gov'

        r = requests.get(self.starting_url)
        soup = bs4.BeautifulSoup(r.content, features="html.parser")

        # get target list items
        policy_list = soup.find('div', attrs={'itemprop': 'articleBody'}).ul

        # extract links
        for link in policy_list.find_all('li')[:-1]:

            yield abs_url(base_url, link.a['href'])


class ICParser(Parser):
    """Parser for Intelligence Community crawler"""

    def parse_docs_from_page(self, page_url: str, page_text: str) -> Iterable[Document]:
        """Parse document objects from page of text"""

        # parse html response
        base_url = 'https://www.dni.gov'
        soup = bs4.BeautifulSoup(page_text, features="html.parser")
        div = soup.find('div', attrs={'itemprop': 'articleBody'})
        pub_list = div.find_all('p')

        # set policy type
        if page_url.endswith('directives'):
            doc_type = 'ICD'
        elif page_url.endswith('guidance'):
            doc_type = 'ICPG'
        elif page_url.endswith('memorandums'):
            doc_type = 'ICPM'
        else:
            doc_type = 'ICLR'

        # iterate through each publication
        parsed_docs = []
        cac_required = ['CAC', 'PKI certificate required', 'placeholder', 'FOUO']
        for row in pub_list:

            # skip empty rows
            if row.a is None:
                continue

            data = re.sub(r'\u00a0', ' ', row.text)
            link = row.a['href']

            # patterns to match
            name_pattern = re.compile(r'^[A-Z]*\s\d*.\d*.\d*.\d*\s')

            parsed_text= re.findall(name_pattern, data)[0]
            parsed_name = parsed_text.split(' ')
            doc_name = ' '.join(parsed_name[:2])
            doc_num = parsed_name[1]
            doc_title = re.sub(parsed_text, '', data)

            pdf_url = abs_url(base_url, link)
            pdf_di = DownloadableItem(
                doc_type='pdf',
                web_url=pdf_url
            )

            # extract publication date from the pdf url
            matches = re.findall(r'\((.+)\)', pdf_url.replace('%20', '-'))
            publication_date = matches[-1] if len(matches) > 0 else None

            # set boolean if CAC is required to view document
            cac_login_required = True if any(x in pdf_url for x in cac_required) \
                                         or any(x in doc_title for x in cac_required) else False

            # all fields that will be used for versioning
            version_hash_fields = {
                "item_currency": publication_date  # version metadata found on pdf links
            }

            doc = Document(
                doc_name=doc_name.strip(),
                doc_title=doc_title,
                doc_num=doc_num,
                doc_type=doc_type,
                publication_date=publication_date,
                cac_login_required=cac_login_required,
                crawler_used="ic_policies",
                source_page_url=page_url.strip(),
                version_hash_raw_data=version_hash_fields,
                downloadable_items=[pdf_di]
            )

            parsed_docs.append(doc)

        return parsed_docs


class ICCrawler(Crawler):
    """Crawler for the example web scraper"""
    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            **kwargs,
            pager=ICPager(
                starting_url=BASE_SOURCE_URL
            ),
            parser=ICParser()
        )


class FakeICCrawler(Crawler):
    """Intelligence Community crawler that just uses stubs and local source files"""
    def __init__(self, *args, **kwargs):
        with open(os.path.join(SOURCE_SAMPLE_DIR, 'ic_policies.html')) as f:
            default_text = f.read()

        super().__init__(
            *args,
            **kwargs,
            pager=ICPager(
                requestor=MapBasedPseudoRequestor(
                    default_text=default_text
                ),
                starting_url=BASE_SOURCE_URL
            ),
            parser=ICParser()
        )
