import bs4
import re
import os
import requests
import json
import datetime
from typing import Iterable
import string
from dataPipelines.gc_crawler.requestors import MapBasedPseudoRequestor
from dataPipelines.gc_crawler.exec_model import Crawler, Parser, Pager
from dataPipelines.gc_crawler.data_model import Document, DownloadableItem
from dataPipelines.gc_crawler.utils import abs_url
from . import SOURCE_SAMPLE_DIR, BASE_SOURCE_URL
from dataPipelines.gc_crawler import CERTIFICATE_DIR



class NavyMedPager(Pager):
    """Pager for DoD Issuance crawler"""

    def iter_page_links(self) -> Iterable[str]:
        """Iterator for page links"""
        base_url = 'https://www.med.navy.mil'
        r = requests.get(self.starting_url, verify=CERTIFICATE_DIR + '/cat3.pem')
        soup = bs4.BeautifulSoup(r.content, features="html.parser")

        # get target column of list items
        issuance_list = soup.find('div', attrs={'class': 'noindex ms-wpContentDivSpace'})
        matches = ["Publications", "BUMEDNotes", "BUMEDInstructions"]
        # extract links
        links = [link for link in issuance_list.find_all('a')]
        for link in links[2:-1]:
            if any(x in str(link) for x in matches):
                if not link['href'].startswith('http'):
                    url = base_url + link['href']
                else:
                    url = link['href']
                yield url


def remove_html_tags(text):
    import re
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)


def hasNumbers(inputString):
    return any(char.isdigit() for char in inputString)


class NavyMedParser(Parser):
    """Parser for DoD Issuance crawler"""

    def parse_docs_from_page(self, page_url: str, page_text: str) -> Iterable[Document]:
        """Parse document objects from page of text"""
        # parse html response
        url = "https://www.med.navy.mil/directives/Pages/Publications.aspx"
        base_url = 'https://www.med.navy.mil'
        parsed_docs = []
        doc_name_list = []
        if (page_url.find("Publications") != -1):
            doc_type = "NAVMED"
        elif (page_url.find("BUMEDNotes") != -1):
            doc_type = "BUMEDNOTE"
        elif (page_url.find("BUMEDInstructions") != -1):
            doc_type = "BUMEDINST"
        cac_required = ['CAC', 'PKI certificate required', 'placeholder', 'FOUO']
        page = requests.get(page_url, verify=CERTIFICATE_DIR + '/cat3.pem')
        soup = bs4.BeautifulSoup(page.content, 'html.parser')
        webpart = soup.find(id="onetidDoclibViewTbl0")
        items = webpart.find_all('a')
        meta = webpart.find_all(lambda tag: tag.name == 'td' and tag.get('class') == ['ms-vb2'])
        meta_list = list(meta)
        meta_list = [remove_html_tags(str(t)) for t in meta_list]
        meta_list = [str(t).encode('ascii', 'ignore').decode('ascii') for t in meta_list]
        meta_list = [x.replace("\r\n", " ") for x in meta_list]
        if (doc_type == "NAVMED"):
            n = 3
        elif (doc_type == "BUMEDINST" or doc_type == "BUMEDNOTE"):
            n = 4
        meta_ = [meta_list[i:i + n] for i in range(0, len(meta_list), n)]
        if (doc_type == "NAVMED"):
            subject = webpart.find_all(lambda tag: tag.name == 'td' and tag.get('class') == ['ms-vb-title'])
            name_list = list(subject)
            name_list = [remove_html_tags(str(t)) for t in name_list]
            name_list = [str(t).encode('ascii', 'ignore').decode('ascii') for t in name_list]
            subnum = [str(t[1]).split()[:2] for t in meta_]
            title_ = [str(t[1]).split()[2:] for t in meta_]
            title = [' '.join(t) for t in title_]
            title = [str(t).replace(',', '') for t in title]
            date = [t[0] for t in meta_]
            metadata = zip(subnum, title, date, name_list)
            metadata = [list(a) for a in metadata]
        elif (doc_type == "BUMEDINST"):
            subject = webpart.find_all(lambda tag: tag.name == 'td' and tag.get('class') == ['ms-vb-title'])
            name_list = list(subject)
            name_list = [remove_html_tags(str(t)) for t in name_list]
            name_list = [str(t).encode('ascii', 'ignore').decode('ascii') for t in name_list]
            metadata = list(zip(name_list, meta_))
        elif (doc_type == "BUMEDNOTE"):
            metadata = meta_
        item_list = list(items)
        pdf_links = [link['href'] for link in item_list if link['href'].endswith(('pdf', 'html'))]
        pdf_links = ["https://www.med.navy.mil" + a for a in pdf_links]
        pdf_links = [str(a).replace(' ', '%20') for a in pdf_links]
        if (doc_type == "BUMEDINST" or doc_type == "BUMEDNOTE"):
            metadata = [list(ele) for ele in metadata]
        for i in range(0, len(metadata)):
            metadata[i].append(pdf_links[i])
        for item in metadata:
            if (doc_type == "NAVMED"):
                pdf_di = DownloadableItem(doc_type='pdf', web_url=item[4])
                if (str(item[3])[0].isdigit()):
                    doc_name = "NAVMED P-" + str(item[3]).split()[0]
                    doc_num = "P-" + str(item[3]).split()[0]
                    if (doc_name in doc_name_list):
                        number_of_times = sum(1 for s in doc_name_list if doc_name in s)
                        doc_name = doc_type + " " + doc_num + "-" + str(number_of_times)
                        doc_num = doc_num + "-" + str(number_of_times)
                else:
                    doc_name = "NAVMED " + str(item[0][1]) + " " + ' '.join(str(item[3]).split()[:3])
                    doc_num == str(item[0][1]) + " " + ' '.join(str(item[3]).split()[:3])
                    if (doc_name in doc_name_list):
                        number_of_times = sum(1 for s in doc_name_list if doc_name in s)
                        doc_name = doc_type + " " + doc_num + "-" + str(number_of_times)
                        doc_num = doc_num + "-" + str(number_of_times)
                doc_title = str(item[1])
                publication_date = str(item[2])
                cac_login_required = False
                crawler_used = "navy_med_pubs"
                source_page_url = page_url
                downloadable_items = [pdf_di]
                version_hash_fields = {
                    "item_currency": str(item[3]).split('/')[-1],  # version metadata found on pdf links
                    "pub_date": publication_date.strip(),
                    "document_title": doc_title.strip(),
                    "document_number": doc_num.strip()
                }

            elif (doc_type == "BUMEDINST"):
                pdf_di = DownloadableItem(doc_type='pdf', web_url=item[2])
                doc_num = str(item[0]).split()[0]
                doc_name = doc_type + " " + doc_num
                doc_title = str(item[1][1])
                publication_date = str(item[1][0])
                if (str(item[2]).endswith('html')):
                    cac_login_required = True
                elif (str(item[2]).endswith('pdf')):
                    cac_login_required = False
                if (doc_name in doc_name_list):
                    number_of_times = sum(1 for s in doc_name_list if doc_name in s)
                    doc_name = doc_type + " " + doc_num + "-" + str(number_of_times)
                    doc_num = doc_num + "-" + str(number_of_times)
                doc_name_list.append(doc_name)
            elif (doc_type == "BUMEDNOTE"):
                pdf_di = DownloadableItem(doc_type='pdf', web_url=item[4])
                doc_num = str(item[0]).split()[1]
                doc_name = doc_type + " " + doc_num
                doc_title = str(item[2])
                publication_date = str(item[1])
                cac_login_required = False
                if (doc_name in doc_name_list):
                    number_of_times = sum(1 for s in doc_name_list if doc_name in s)
                    doc_name = doc_type + " " + doc_num + "-" + str(number_of_times)
                    doc_num = doc_num + "-" + str(number_of_times)
                doc_name_list.append(doc_name)
            version_hash_fields = {
                "doc_name": doc_name,  # version metadata found on pdf links
                "pub_date": publication_date.strip(),
                "document_title": doc_title.strip(),
                "document_number": doc_num.strip()
            }
            version_hash_raw_data = version_hash_fields
            doc = Document(
                doc_name=re.sub(',', '', doc_name.strip()),
                doc_title=re.sub('\\"', '', doc_title),
                doc_num=re.sub(',', '', doc_num.strip()),
                doc_type=re.sub(',', '', doc_type.strip()),
                publication_date=publication_date,
                cac_login_required=cac_login_required,
                crawler_used="navy_med_pubs",
                source_page_url=page_url.strip(),
                version_hash_raw_data=version_hash_fields,
                downloadable_items=[pdf_di]
            )
            parsed_docs.append(doc)
        return parsed_docs


class NavyMedCrawler(Crawler):
    """Crawler for the example web scraper"""

    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            **kwargs,
            pager=NavyMedPager(
                starting_url=BASE_SOURCE_URL
            ),
            parser=NavyMedParser()
        )


class FakeNavyMedCrawler(Crawler):
    """DoD Issuance crawler that just uses stubs and local source files"""

    def __init__(self, *args, **kwargs):
        with open(os.path.join(SOURCE_SAMPLE_DIR, 'navy_med_pubs.html')) as f:
            default_text = f.read()
        super().__init__(
            *args,
            **kwargs,
            pager=NavyMedPager(
                requestor=MapBasedPseudoRequestor(
                    default_text=default_text
                ),
                starting_url=BASE_SOURCE_URL
            ),
            parser=NavyMedParser()
        )
