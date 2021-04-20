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


class BupersPager(Pager):
    """Pager for Bupers crawler"""

    def iter_page_links(self) -> Iterable[str]:
        """Iterator for page links"""
        yield self.starting_url

class BupersParser(Parser):
    """Parser for Bupers Issuance crawler"""

    def parse_docs_from_page(self, page_url: str, page_text: str) -> Iterable[Document]:
        """Parse document objects from page of text"""

        r = requests.get(page_url)
        soup = bs4.BeautifulSoup(r.content, features="html.parser")
        name = soup.find(id='dnn_CenterPane_Top').find('a')['name']
        pdf_url = soup.find(id='LiveHTMLWrapper' + name).find_all('a')
        pdf_url = [("https://www.mynavyhr.navy.mil" + item['href']).replace(' ', '%20') for item in pdf_url]

        new_url = []
        for i in range(len(pdf_url)):
            if pdf_url[
                i] == 'https://www.mynavyhr.navy.mil/Portals/55/Reference/Instructions/BUPERS/BUPERSINST_12410.25.pdf?ver=mKLgKvdYUIaubAZs0PbkUg%3d%3d':
                pass
            elif pdf_url[i] not in new_url and (pdf_url[i][-4:] != "docx"):
                new_url.append(pdf_url[i])
        pdf_url = new_url
        l = soup.find(id='LiveHTMLWrapper' + name).find_all(attrs={'style': 'font-size: 12px;'})

        nums = []
        titles = []
        dates = []
        bupcount = 0
        for index, val in enumerate(l):
            try:
                # checking for 1640.20B. first document doesn't have a link, but CH-1 does.
                if val.text.replace('\xa0', ' ').split('\n')[-1] == "1640.20B CH-1":
                    nums.append(val.text.replace('\xa0', ' ').split('\n')[-1])
                    titles.append(
                        l[index + 1].text.strip().replace('\xa0', '').replace('-', '').replace('\n', '').replace(
                            '\u200b', ''))
                    dates.append(l[index + 2].text.replace('\u200b', '').strip().split('\n')[-1])

                # CH-1 for 5450.49D doesn't have a link associated with it
                elif val.text.split('\n')[-1] == "5450.49D CH-1":
                    nums.append(
                        val.text.replace('\xa0', '').replace('-', '').replace('\u200b', '').replace('  ', "").split(
                            '\n')[0])
                    titles.append(
                        l[index + 1].text.strip().replace('\xa0', '').replace('-', '').replace('\n', '').replace(
                            '\u200b', ''))
                    dates.append(l[index + 2].text.replace('\u200b', '').strip().split('\n')[0])

                # checking for the repeated BUPERSNOTE 5215 files
                # for the 2nd repeated file, title/date don't appear
                elif val.text.replace('\xa0', '').replace('-', '').replace('\u200b', '').replace('\n', '').replace('  ',
                                                                                                                   "") == "BUPERSNOTE 5215":
                    if bupcount > 0:
                        nums.append(val.text.replace('\xa0', '').replace('-', '').replace('\u200b', '').replace('\n',
                                                                                                                '').replace(
                            '  ', "") + "(2)")
                        titles.append("Cancellation of BUPERSINST 7040.6B")
                        dates.append("12/7/2020")
                    else:
                        nums.append(val.text.replace('\xa0', '').replace('-', '').replace('\u200b', '').replace('\n',
                                                                                                                '').replace(
                            '  ', ""))
                        titles.append(
                            l[index + 1].text.strip().replace('\xa0', '').replace('-', '').replace('\n', '').replace(
                                '\u200b', ''))
                        dates.append(l[index + 2].text.replace('\u200b', '').strip().split('\n')[0])
                    bupcount += 1

                # checking for the 1900.8E docs. the other 2 chapters don't have links
                elif val.text.split('\n')[-1] == "1900.8E CH-2":
                    nums.append(val.text.split('\n')[0])
                    titles.append(
                        l[index + 1].text.strip().replace('\xa0', '').replace('-', '').replace('\n', '').replace(
                            '\u200b', ''))
                    dates.append(l[index + 2].text.replace('\u200b', '').strip().split('\n')[0])

                # checking for the Women's correction program, 1640.27. this file doesn't have a title in the correct format
                elif val.text.replace('\xa0', '').replace('-', '').replace('\u200b', '').replace('\n', '') == "1640.27":
                    nums.append(val.text.replace('\xa0', '').replace('-', '').replace('\u200b', '').replace('\n', ''))
                    titles.append("Women's Correction Program")
                    dates.append(l[index + 1].text.replace('\u200b', '').strip())

                # checking for the BUPERSNOTE file. This is the only file number that starts with a word, not a number.
                elif val.text.replace('\xa0', '').replace('-', '').replace('\u200b', '').replace('\n', '')[
                     0:10] == "BUPERSNOTE":
                    nums.append(
                        val.text.replace('\xa0', '').replace('-', '').replace('\u200b', '').replace('\n', '').replace(
                            "  ", ""))
                    titles.append(
                        l[index + 1].text.strip().replace('\xa0', '').replace('-', '').replace('\n', '').replace(
                            '\u200b', ''))
                    dates.append(l[index + 2].text.replace('\u200b', '').strip())

                # checking for all other files:
                elif int(val.text.replace('\xa0', '').replace('-', '').replace('\u200b', '').split('.')[0]):
                    if val.text.strip().replace('\xa0', '').replace('-', '').replace('\u200b', '').split('\n')[0] in (
                    "1401.5C", "1730.11A", "5800.1A", "1640.20B"):
                        if val.text.strip().replace('\xa0', '').replace('-', '').replace('\u200b', '').split('\n')[
                            0] == "1640.20B":
                            pass
                        else:
                            nums.append(
                                val.text.strip().replace('\xa0', '').replace('-', '').replace('\u200b', '').split('\n')[
                                    0])
                            titles.append(
                                l[index + 1].text.strip().replace('\xa0', '').replace('-', '').replace('\u200b', ''))
                            if val.text.strip().replace('\xa0', '').replace('-', '').replace('\u200b', '').split('\n')[
                                0] == "5800.1A":
                                dates.append(l[index + 2].text.replace('\u200b', '').strip().split('\n')[0])
                            else:
                                dates.append(l[index + 2].text.replace('\u200b', '').strip())
                    elif len(val.text.split('\n')) > 1:
                        # for each repeated document
                        if val.text.strip().replace('\xa0', '').replace('-', '').replace('\u200b', '').split('\n')[
                            1] in ("Vol 1", "Vol 2"):
                            nums.append(" ".join(
                                val.text.strip().replace('\xa0', '').replace('-', '').replace('\u200b', '').split(
                                    '\n')))
                            titles.append(l[index + 1].text)
                            dates.append(l[index + 2].text.replace('\u200b', '').split('\n')[0].strip())
                        else:
                            for n in val.text.strip().replace('\xa0', '').replace('-', '').replace('\u200b', '').split(
                                    '\n'):
                                # append the doc nums
                                nums.append(n)
                                titles.append(l[index + 1].text)
                            for n in l[index + 2].text.strip().replace('\u200b', '').split('\n'):
                                # append the dates
                                dates.append(n.strip())
                    else:
                        nums.append(val.text.strip().replace('\xa0', '').replace('-', '').replace('\u200b', ''))
                        titles.append(
                            l[index + 1].text.strip().replace('\xa0', '').replace('-', '').replace('\u200b', ''))
                        dates.append(l[index + 2].text.replace('\u200b', '').strip())
            except:
                pass

        parsed_docs = []
        for i in range(len(pdf_url)):
            dtype = "BUPERSINST"
            dnum = nums[i]
            dtitle = titles[i].replace("\u00a0", " ").replace("\u200b", "").replace('\n  ', "").strip()
            dname = dtype + " " + dnum
            cac_login_required = False
            publication_date = dates[i]
            url = pdf_url[i]
            pdf_di = DownloadableItem(doc_type='pdf', web_url=url)
            version_hash_fields = {
                "item_currency": url.split('/')[-1].split('?')[0],  # version metadata found on pdf links
                "document_title": dtitle,
                "document_number": dnum.strip()
            }
            doc = Document(
                doc_name=dname.strip(),
                doc_title=dtitle,
                doc_num=dnum.strip(),
                doc_type=dtype,
                publication_date=publication_date,
                cac_login_required=cac_login_required,
                crawler_used="Bupers_Crawler",
                source_page_url=page_url.strip(),
                version_hash_raw_data=version_hash_fields,
                downloadable_items=[pdf_di]
            )

            parsed_docs.append(doc)

        return parsed_docs


class BupersCrawler(Crawler):
    """Crawler for the example web scraper"""

    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            **kwargs,
            pager=BupersPager(
                starting_url=BASE_SOURCE_URL
            ),
            parser=BupersParser()
        )


class FakeBupersCrawler(Crawler):
    """Bupers crawler that just uses stubs and local source files"""

    def __init__(self, *args, **kwargs):
        with open(os.path.join(SOURCE_SAMPLE_DIR, 'bupers_pubs.html')) as f:
            default_text = f.read()

        super().__init__(
            *args,
            **kwargs,
            pager=BupersPager(
                requestor=MapBasedPseudoRequestor(
                    default_text=default_text
                ),
                starting_url=BASE_SOURCE_URL
            ),
            parser=BupersCrawler()
        )
