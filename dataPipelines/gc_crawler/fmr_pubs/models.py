import os
import bs4
from typing import Iterable
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from dataPipelines.gc_crawler.requestors import MapBasedPseudoRequestor
from dataPipelines.gc_crawler.exec_model import Crawler, Parser, Pager
from dataPipelines.gc_crawler.data_model import Document, DownloadableItem

from . import SOURCE_SAMPLE_DIR, BASE_SOURCE_URL


class FMRPager(Pager):
    """Pager for FMR crawler"""

    def iter_page_links(self) -> Iterable[str]:
        """Iterator for page links"""
        r = requests.get(self.starting_url)
        soup = bs4.BeautifulSoup(r.content, 'html.parser')
        m = soup.find(id='sitetitle').find_all('a')
        d = [i.get_text() for i in m]

        for vol in d[1:-1]:
            yield 'https://comptroller.defense.gov/FMR/vol{}_chapters.aspx'.format(vol)


class FMRParser(Parser):
    """Parser for FMR crawler"""

    def parse_docs_from_page(self, page_url: str, page_text: str) -> Iterable[Document]:
        """Parse document objects from page of text"""
        r = requests.get(page_url)
        soup = bs4.BeautifulSoup(r.content, 'html.parser')

        ch = soup.find_all('td', attrs={'width':79})
        li = []
        for j in ch:
            try:
                li.append('https://comptroller.defense.gov' + j.find('a')['href'])
            except:
                # if exception then the doc is archived, so there's no link
                li.append(None)
                #continue

        ch = [m.get_text() for m in ch]  # the chapters
        de = soup.find_all('td', attrs={'width':340})  # the titles/summaries of each document
        # cleaning the titles:
        de = [' '.join(m.get_text().replace('\n', '').split()) for m in de]
        de = [m[:m.find('(')].rstrip() for m in de]

        # lots of messy things with the dates, so adjustments were needed:
        s = soup.find(class_='para')

        if page_url[39:41] == "6A":
            # I really don't like this method, would prefer find_all(width=102) if vol6A didn't have issues
            da = s.find_all('td')[2::3]
        else:
            da = s.find_all(width=102)

        da = [" ".join(m.get_text().replace('\xa0', ' ').split()) for m in da]

        # removing archives
        indices = [i for i, x in enumerate(li) if x == None]
        for i in indices[::-1]:
            del ch[i]
            del li[i]
            del de[i]
            del da[i]

        # individual case
        try:
            if int(s.find('h2').get_text().split()[1]) == 16:
                de[-1] = "Definitions"
        except:
            pass

        parsed_docs = []
        for i, j in enumerate(ch):
            doc_name = ' '.join(s.find('h2').get_text().split()[:2]) + ', ' + ch[i].replace('\u00a0', '') + ' : ' + f'"{de[i]}"'
            doc_num = "V{}CH{}".format(s.find('h2').get_text().split()[1], j.split()[-1][:3])
            doc_type = li[i][li[i].rfind('.') + 1:]
            web_url = li[i]
            pub_date = da[i]

            version_hash_fields = {
                "original_title": doc_name,
                "pub_date": pub_date
            }

            dl = DownloadableItem(
                    doc_type=doc_type,
                    web_url=web_url
                )

            doc = Document(
                doc_name="DoDFMR "+doc_num,
                doc_title=doc_name,
                doc_num=doc_num,
                doc_type="DoDFMR",
                source_page_url=page_url,
                publication_date=pub_date,
                cac_login_required=False,
                version_hash_raw_data=version_hash_fields,
                downloadable_items=[dl],
                crawler_used="fmr_pubs"
            )

            parsed_docs.append(doc)

        return parsed_docs


class FMRCrawler(Crawler):
    """Crawler for the FMR web scraper"""
    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            **kwargs,
            pager=FMRPager(
                starting_url=BASE_SOURCE_URL
            ),
            parser=FMRParser()
        )


class FakeFMRCrawler(Crawler):
    """FMR crawler that just uses stubs and local source files"""
    def __init__(self, *args, **kwargs):
        with open(os.path.join(SOURCE_SAMPLE_DIR, "fmr_pubs.html")) as f:
            default_text = f.read()

        super().__init__(
            *args,
            **kwargs,
            pager=FMRPager(
                requestor=MapBasedPseudoRequestor(
                    default_text=default_text
                ),
                starting_url=BASE_SOURCE_URL
            ),
            parser=FMRParser()
        )
