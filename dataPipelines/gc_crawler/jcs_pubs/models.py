import bs4
import re
from re import search
import os
import requests
from typing import Iterable

from dataPipelines.gc_crawler.requestors import MapBasedPseudoRequestor
from dataPipelines.gc_crawler.exec_model import Crawler, Parser, Pager
from dataPipelines.gc_crawler.data_model import Document, DownloadableItem

from . import SOURCE_SAMPLE_DIR, BASE_SOURCE_URL


class JCSPager(Pager):
    """Pager for JCS crawler"""

    def iter_page_links(self) -> Iterable[str]:
        """Iterator for page links"""

        r = requests.get(self.starting_url)
        soup = bs4.BeautifulSoup(r.content, features="html.parser")
        nav_bar = soup.find_all('ul', attrs={'class': 'dropdown-menu'})

        # get target column of list items
        pub_list = nav_bar[3]

        # extract links
        for li_tag in pub_list.find_all('li')[1:-1]:

            link = li_tag.a
            page_text = requests.get(link['href']).content

            # find the number of pages in the table
            soup = bs4.BeautifulSoup(page_text, features="html.parser")
            tables = soup.find_all('table', attrs={'class': 'dnnFormItem'})
            pages = tables[1]

            if pages.a is None:

                yield link['href']
            else:
                page_ext = pages.find_all('a')[-1]['href'][:-1]
                num_pages = pages.find_all('a')[-1]['href'][-1]
                for page in range(1, int(num_pages) + 1):

                    yield link['href'] + page_ext + str(page)


class JCSParser(Parser):
    """Parser for JCS crawler"""

    def parse_docs_from_page(self, page_url: str, page_text: str) -> Iterable[Document]:
        """Parse document objects from page of text"""

        # parse html response
        encoded_str = page_text.encode('ascii', 'ignore')
        soup = bs4.BeautifulSoup(encoded_str, features="html.parser")
        tables = soup.find_all('table', attrs={'class': 'dnnFormItem'})
        rows = tables[0].tbody.find_all('tr')

        # set document type
        if search('Instructions', page_url):
            doc_type = 'CJCSI'
        elif search('Manuals', page_url):
            doc_type = 'CJCSM'
        elif search('Notices', page_url):
            doc_type = 'CJCSN'
        else:
            doc_type = 'CJCS GDE'

        # iterate through each row of the table
        parsed_docs = []
        cac_required = ['CAC', 'PKI certificate required', 'placeholder', 'FOUO']
        for row in rows[1:]:

            # reset variables to ensure there is no carryover between rows
            doc_num = ''
            doc_name = ''
            doc_title = ''
            publication_date = ''
            cac_login_required = False
            pdf_url = ''
            pdf_di = None



            pdf_url = row.td.a['href'].strip()
            doc_name = row.td.a.text.strip()

            doc_num_matcher = re.match(r"(?P<doc_type>(\s*\w+)*?)\s+(?P<doc_num>([0-9]+[a-zA-Z0-9.-_]*)+)", doc_name)
            if doc_num_matcher:
                doc_num = doc_num_matcher.groupdict()['doc_num']
            else:
                doc_num = doc_name.split(' ')[-1]

            doc_title = row.find('td', attrs={'class': 'DocTitle'}).text.strip()
            publication_date = row.find('td', attrs={'class': 'DocDateCol'}).text.strip()

            pdf_di = DownloadableItem(
                doc_type='pdf',
                web_url=BASE_SOURCE_URL + pdf_url
            )

            # set boolean if CAC is required to view document
            cac_login_required = True if any(x in pdf_url for x in cac_required) \
                                              or any(x in doc_title for x in cac_required) else False

            # all fields that will be used for versioning
            version_hash_fields = {
                "item_currency": row.find('td', attrs={'class': 'CurrentCol'}).text.strip(),
                "pub_description": re.sub('\\"', '', row.find('td', attrs={'class': 'DocInfoCol'}).img['title'].strip())
            }

            doc = Document(
                doc_name=doc_name.strip(),
                doc_title=re.sub('\\"', '', doc_title),
                doc_num=doc_num.strip(),
                doc_type=doc_type.strip(),
                publication_date=publication_date,
                cac_login_required=cac_login_required,
                crawler_used="jcs_pubs",
                source_page_url=page_url.strip(),
                version_hash_raw_data=version_hash_fields,
                downloadable_items=[pdf_di]
            )

            parsed_docs.append(doc)

        return parsed_docs


class JCSCrawler(Crawler):
    """Crawler for the example web scraper"""
    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            **kwargs,
            pager=JCSPager(
                starting_url=BASE_SOURCE_URL
            ),
            parser=JCSParser()
        )


class FakeJCSCrawler(Crawler):
    """JCS crawler that just uses stubs and local source files"""
    def __init__(self, *args, **kwargs):
        with open(os.path.join(SOURCE_SAMPLE_DIR, 'jcs_pubs.html'), encoding='utf-8') as f:
            default_text = f.read()

        super().__init__(
            *args,
            **kwargs,
            pager=JCSPager(
                requestor=MapBasedPseudoRequestor(
                    default_text=default_text
                ),
                starting_url=BASE_SOURCE_URL
            ),
            parser=JCSParser()
        )
