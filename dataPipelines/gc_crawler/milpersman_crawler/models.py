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
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from . import SOURCE_SAMPLE_DIR, BASE_SOURCE_URL


class MilpersPager(Pager):
    """Pager for Milpers Issuance crawler"""

    def iter_page_links(self) -> Iterable[str]:
        """Iterator for page links"""
        r = requests.get(self.starting_url)
        soup = bs4.BeautifulSoup(r.content, features="html.parser")
        meta = soup.find(id="dnn_LeftPane").find_all('a')

        # excluding the first element because it's garbage text
        # excluding the last because I don't know if it was included in the original implementation
        # TODO:
        #  check if http://www.mynavyhr.navy.mil/References/MILPERSMAN/Updated-New-Cancelled-Articles/
        #  is used for the implementation
        links = [item['href'] for item in meta[1:-1] if "MILPERSMAN" in item['href']]

        # for the 1000-1999 docs, they have seperate links. everything else doesn't
        r = requests.get(links[0])
        soup = bs4.BeautifulSoup(r.content, features="html.parser")
        meta2 = soup.find(id='LiveHTMLWrapper34769').find_all('a')
        links2 = ['https://www.mynavyhr.navy.mil' + item['href'] for item in meta2]  # weird, ugly formatting
        links = links2 + links[1:-1]

        for link in links:
            yield link

class MilpersParser(Parser):
    """Parser for Milpers Issuance crawler"""

    def parse_docs_from_page(self, page_url: str, page_text: str) -> Iterable[Document]:
        """Parse document objects from page of text"""
        r = requests.get(page_url)
        soup = bs4.BeautifulSoup(r.content, features="html.parser")

        name = soup.find(id='dnn_CenterPane_Top').find('a')['name']
        pdf_url = soup.find(id='LiveHTMLWrapper' + name).find_all('a')
        pdf_url = [("https://www.mynavyhr.navy.mil" + item['href']).replace(' ', '%20') for item in pdf_url]

        new_url = []
        for i in range(len(pdf_url)):
            if pdf_url[i] not in new_url:
                new_url.append(pdf_url[i])
        for i in range(len(new_url)):
            if "1910-153.pdf" in new_url[i]:
                del new_url[i]
                break
        pdf_url = new_url

        l = soup.find(id='LiveHTMLWrapper' + name).find_all(attrs={'style': 'font-size: 12px;'})

        # the main loop to get nums, the document numbers, and titles, the titles of the docs
        nums = []
        titles = []
        for index, val in enumerate(l):
            try:
                # there's a couple special cases we need to check for the 1000 and 1900 documents.

                # special case in the 1000 docs, one doc has an "Exhibit" document that goes with it.
                if "Exhibit" in val.text:
                    nums.append(nums[-1] + "Exhibit")
                    titles.append(val.text)

                # checking the 1900s documents for special cases. checking because it's broken html
                # whose doc nums/titles needs to be hard-coded in. check this in case anything breaks in the future
                # NOTE: 1000-160, 1320-170, and 1600-090, 1200-070 all lead to the incorrect PDF on the website. This might
                # get corrected in the future, in which case we'll remove some of these lines that exclude documents
                elif int(val.text.replace('\xa0', '').replace('-', '').replace('\u200b', '').split()[0]) == 1910153:
                    pass
                elif int(val.text.replace('\xa0', '').replace('-', '').replace('\u200b', '').split()[0]) == 1000160:
                    pass
                elif int(val.text.replace('\xa0', '').replace('-', '').replace('\u200b', '').split()[0]) == 1600090:
                    pass
                elif int(val.text.replace('\xa0', '').replace('-', '').replace('\u200b', '').split()[0]) == 1320170:
                    pass
                elif int(val.text.replace('\xa0', '').replace('-', '').replace('\u200b', '').split()[0]) == 19:
                    pass
                elif int(val.text.replace('\xa0', '').replace('-', '').replace('\u200b', '').split()[0]) == 1640:
                    pass
                elif int(val.text.replace('\xa0', '').replace('-', '').replace('\u200b', '').split()[0]) == 10412:
                    nums.append('1910-412')
                    titles.append(l[index + 1].text)
                    pass
                elif int(val.text.replace('\xa0', '').replace('-', '').replace('\u200b', '').split()[0]) == 1916:
                    pass

                # now that the special cases are checked, for everything else:
                elif int(val.text.replace('\xa0', '').replace('-', '').replace('\u200b', '').split()[0]) or (
                        "Exhibit" in val.text.replace('-', '')):
                    # checking to make sure the document isn't cancelled. if it is, then we skip it. else, append
                    # the doc num and title
                    if l[index + 1].text.replace('\xa0', '').replace('-', '').replace('\u200b', '') not in ("Cancelled", "Suspended"):
                        nums.append(val.text.replace('\xa0', '').replace('\u200b', '').split()[0])
                        titles.append(l[index + 1].text)
            except:
                pass

        # cleaning the titles, removing bad spaces and extra characters not supposed to be there
        for i in range(len(titles)):
            titles[i] = titles[i].replace('\n  ', '').replace('\xa0', ' ')

        if len(titles) == len(pdf_url) == len(nums):
            pass
        else:
            raise Exception(f"Incorrect iteration in {page_url}")

        # the final document retrieval
        parsed_docs = []
        for i in range(len(pdf_url)):
            dtype = "MILPERSMAN"
            dnum = nums[i]
            dtitle = titles[i].replace('\u200b', '').replace('\u2013 ', '').replace('\u2013', '').replace('\u2019', '').replace('\n', '').replace('\u201c', '').replace('\u201d', '')
            dname = dtype + " " + dnum
            cac_login_required = False
            publication_date = "N/A"
            url = pdf_url[i]
            pdf_di = DownloadableItem(doc_type='pdf', web_url=url)
            version_hash_fields = {
                "item_currency": url.split('/')[-1].split('?')[0],  # version metadata found on pdf links
                "document_title": dtitle.strip(),
                "document_number": dnum.strip()
            }
            doc = Document(
                doc_name=dname.strip(),
                doc_title=dtitle,
                doc_num=dnum.strip(),
                doc_type=dtype,
                publication_date=publication_date,
                cac_login_required=cac_login_required,
                crawler_used="milpersman_crawler",
                source_page_url=page_url.strip(),
                version_hash_raw_data=version_hash_fields,
                downloadable_items=[pdf_di]
            )

            parsed_docs.append(doc)

        return parsed_docs


class MilpersCrawler(Crawler):
    """Crawler for the example web scraper"""
    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            **kwargs,
            pager=MilpersPager(
                starting_url=BASE_SOURCE_URL
            ),
            parser=MilpersParser()
        )


class FakeMilpersCrawler(Crawler):
    """Milpersman crawler that just uses stubs and local source files"""
    def __init__(self, *args, **kwargs):
        with open(os.path.join(SOURCE_SAMPLE_DIR, 'milpersman_crawler.html')) as f:
            default_text = f.read()

        super().__init__(
            *args,
            **kwargs,
            pager=MilpersPager(
                requestor=MapBasedPseudoRequestor(
                    default_text=default_text
                ),
                starting_url=BASE_SOURCE_URL
            ),
            parser=MilpersParser()
        )
