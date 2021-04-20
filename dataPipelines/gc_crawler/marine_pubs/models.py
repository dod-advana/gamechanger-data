import bs4
import re
import os
from datetime import datetime
from typing import Iterable, Tuple
from common.utils.text_utils import trim_string

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains

from dataPipelines.gc_crawler.requestors import MapBasedPseudoRequestor
from dataPipelines.gc_crawler.exec_model import Crawler, Parser, Pager
from dataPipelines.gc_crawler.data_model import Document, DownloadableItem
from dataPipelines.gc_downloader.string_utils import normalize_string

from . import SOURCE_SAMPLE_DIR, BASE_SOURCE_URL, driver


class MCPager(Pager):
    """Pager for Marine Corps crawler"""

    def iter_page_links(self) -> Iterable[str]:
        """Iterator for page links"""
        pass

    def iter_page_links_with_text(self) -> Iterable[Tuple[str, str]]:

        # use the webdriver to get url
        driver.get(self.starting_url)

        # extract the last page number
        WebDriverWait(driver, 20).until(ec.presence_of_element_located((By.XPATH, "//*[@class='pagination']")))

        # extract the page text
        first_html = driver.execute_script("return document.documentElement.outerHTML")
        soup = bs4.BeautifulSoup(first_html, features="html.parser")

        # extract the pagination pane
        page_list = soup.find("ul", attrs={"class": "pagination"}).find_all('li')

        # extract the last page number
        last_page = int(page_list[-1].text.strip())
        next_page_num = 1

        # loop through pages until the last
        while next_page_num <= last_page:

            if next_page_num != 1:
                # extract the next link
                next_button = WebDriverWait(driver, 20).until(
                    ec.presence_of_element_located((By.XPATH, "//*[@class='fas fa fa-angle-right da_next_pager']")))
                ActionChains(driver).move_to_element(next_button).perform()
                next_button.click()

            # increase next page tracker
            next_page_num += 1

            # yield page url and text
            html_list = []
            html = driver.execute_script("return document.documentElement.outerHTML")
            html_list.append((driver.current_url, html))
            yield html_list[-1]


class MCParser(Parser):
    """Parser for Marine Corps crawler"""

    def parse_docs_from_page(self, page_url: str, page_text: str) -> Iterable[Document]:
        """Parse document objects from page of text"""

        # parse html response
        soup = bs4.BeautifulSoup(page_text, features="html.parser")
        rows = soup.find_all('div', attrs={'class': 'litem'})

        # list of CAC restricted characteristics
        cac_required = ["placeholder", "FOUO", "for_official_use_only"]

        # iterate through each row of the table
        parsed_docs = []
        for row in rows[1:]:

            # TYPE
            tbl_type = row.find("div", attrs={"class": "list-type"}).text.upper()

            # TITLE
            tbl_title = row.find("div", attrs={"class": "list-title"}).text.upper()

            # SUMMARY
            tbl_summary = row.find("div", attrs={"class": "cat"}).text.upper()

            # STATUS
            tbl_status = row.find("div", attrs={"class": "status"}).text.upper()

            # skip deleted pubs
            if tbl_status == "DELETED" or len(tbl_title) == 0 or tbl_title == "FED LOG" or "POSTER" in tbl_title \
                    or "ROAD MAPS" in tbl_title:
                continue

            # patterns to extract
            type_pattern = re.compile("^[A-Z]+")
            type_spc_pattern = re.compile("^[A-Z ]+")
            num_pattern = re.compile("[0-9].*")
            alpha_num_pattern = re.compile("[((A-Z-)?(0-9))].+")
            part_pattern = re.compile(r"(PT(\s)?\d)|((_|\s)\d)")

            # title patterns to remove
            rm_date = r"(\d+[A-Z]{3}(\d{4}|\d{2}))"
            rm_with = "(W/)|(WITH)|(W-)|(&#39;)|(AMP;)"
            rm_idx = r"(/INDEX)|(.PDF)|( -)"
            rm_canx = r"(\(|CANCEL|DTD|CANX|FORMER).+"
            rm_spc = r"\s*[\n\t\r\s+]\s*"
            rm_char = r"[^a-zA-Z0-9 ()\\-]"
            rm_matches = "|".join([rm_date,rm_with, rm_idx, rm_canx])

            # DOCUMENT TITLE
            doc_title = re.sub(rm_spc, " ", tbl_summary).strip()

            # go to details page
            driver.get(row.a["href"])

            # wait for page to load
            WebDriverWait(driver, 30).until(
                ec.visibility_of_element_located((By.XPATH, "//*[@class='msg-title msg-title-animate']")))

            # extract HTML from detail page
            html = driver.execute_script("return document.documentElement.outerHTML")
            soup = bs4.BeautifulSoup(html, features="html.parser")

            # extract detail title
            dtl_title = soup.find("div", attrs={"class": "msg-title msg-title-animate"}).text.strip().upper()

            # extract pdf link
            url_pattern = re.compile("^https?://\\S+$")
            pdf_tags = soup.find_all("a", attrs={"class": "button-primary dark"})

            # skip publications without document links
            if not pdf_tags:
                # go back to publications table
                driver.execute_script("window.history.go(-1)")
                continue

            # check if links are the same
            dup_links = all(tag == pdf_tags[0] for tag in pdf_tags)

            for pdf_tag in pdf_tags:

                # extract pdf title
                pdf_title = pdf_tag["title"].upper()

                # skip if no link exists or the document isn't loaded
                if pdf_title == "" or "NOTLOADED" in pdf_title \
                        or pdf_tag["href"] == "" or pdf_tag["href"] == "http://":
                    continue

                # transform title
                title = re.sub(rm_matches, "", pdf_title).strip()
                dtl_title = re.sub(rm_matches, "", dtl_title).strip()

                # delete unwanted characters
                title = normalize_string(title)
                dtl_title = normalize_string(dtl_title)

                # DOCUMENT NAME, handle cases where pub name not in pdf title
                dtl_list = dtl_title.split()
                if len(dtl_list) > 1:
                    if dtl_list[0] not in title and dtl_list[1] not in title:
                        doc_name = " ".join(dtl_list[:2]) + " " + title
                    elif dtl_list[0] not in title and dtl_list[1] in title:
                        doc_name = dtl_list[0] + " " + title
                    else:
                        doc_name = title
                elif dtl_list[0] not in title:
                    doc_name = dtl_list[0] + " " + title
                else:
                    doc_name = title

                # handle special case
                if title == "MCO 3500.59C":
                    doc_name = dtl_title

                # DOCUMENT NAME, TYPE & NUMBER
                if title.startswith("DA ") or tbl_type.startswith("NAVMC D"):
                    doc_type = type_spc_pattern.findall(doc_name)[0].strip()
                    doc_num = doc_name.split(doc_type)[1].strip()

                elif title.startswith("IRM"):
                    doc_type = type_pattern.findall(doc_name)[0].strip()
                    doc_num = doc_name.split(doc_type)[1].strip()

                elif title.startswith("MANUAL FOR COURTS"):
                    doc_type = "MANUAL"
                    doc_num = ""
                    doc_name = trim_string(title, 100)

                elif title.startswith("DCG"):
                    doc_type = "DCG"
                    doc_num = dtl_title.split(doc_type)[1].strip()
                    doc_name = " ".join((doc_type, doc_num))

                elif dtl_title.startswith("FORTITU"):
                    doc_type = "MISC PUBS"
                    doc_num = doc_name.split(dtl_list[0])[1].strip()

                elif title.startswith("SECNAV"):
                    doc_type = type_pattern.findall(doc_name)[0].strip()
                    doc_num = doc_name.split(doc_type)[1].strip()

                elif tbl_type == "HISTORICAL":
                    # extract part number to append to truncated titles
                    part_num = part_pattern.findall(title)[0][0] if part_pattern.findall(title) else None

                    # truncate long titles
                    doc_name = trim_string(title, 100)

                    doc_type = "MISC PUBS"
                    doc_num = ''

                    # only replace long titles with part number (if exists)
                    doc_name = re.sub("("+doc_name.split(" ")[-1]+"$)", part_num, title) \
                        if part_num and len(doc_name) > 100 else doc_name

                elif tbl_type in ["UM", "MISC PUBS"]:
                    doc_type = tbl_type
                    doc_num = ""
                    doc_name = trim_string(doc_name, 100)

                elif tbl_type == "ARMY PUBS":
                    doc_type = type_spc_pattern.findall(doc_name)[0].strip()
                    doc_num = doc_name.split(doc_type)[1].strip()

                elif tbl_type == "MCO P":
                    doc_type = tbl_type
                    if "SECTION" in dtl_title:
                        doc_num = dtl_title.split(doc_type)[1].strip()
                        doc_name = " ".join((doc_type, doc_num))
                    else:
                        doc_num = doc_name.split(doc_type)[1].strip()
                    doc_name = re.sub('(\sTHRU\s)', '-', doc_name)

                elif "NAVY REGULATIONS" in title:
                    doc_type = "MISC PUBS"
                    doc_num = ""
                    doc_name = trim_string(title, 100)

                else:
                    doc_type = type_pattern.findall(doc_name)[0].strip()
                    doc_num = doc_name.split(doc_type)[1].strip()

                # PUBLICATION DATE
                detail = soup.find("div", attrs={"class": "msg-details msg-details-animate"}).text.split("|")
                pub_date = re.sub(rm_spc, " ", detail[0]).strip()
                pub_date = datetime.strptime(pub_date, "%d %b %Y").strftime("%Y-%m-%d")

                # extract downloadable item
                pdf_url = pdf_tag["href"].replace(" ", "%20") if len(pdf_tag) != 0 else page_url

                pdf_di = DownloadableItem(
                    doc_type="pdf",
                    web_url=pdf_url if url_pattern.findall(pdf_url) else BASE_SOURCE_URL + pdf_url
                )

                # set boolean if CAC is required to view document
                cac_login_required = True if any(x in doc_title for x in cac_required) or pdf_url == page_url else False

                # all fields that will be used for versioning
                version_hash_fields = {
                    "item_currency": pdf_url.split("/")[-1],  # version metadata found on pdf links
                    "summary": tbl_summary,
                    "original_title": tbl_title,
                    "pub_date": pub_date
                }

                # store information in document object
                doc = Document(
                    doc_name=doc_name,
                    doc_title=re.sub(rm_char, "", doc_title),
                    doc_num=doc_num,
                    doc_type=doc_type,
                    publication_date=pub_date,
                    cac_login_required=cac_login_required,
                    source_page_url=page_url.strip(),
                    version_hash_raw_data=version_hash_fields,
                    downloadable_items=[pdf_di],
                    crawler_used="marine_pubs"
                )

                # append document to the document list
                parsed_docs.append(doc)

                # skip duplicate links
                if dup_links:
                    break

            # go back to publications table
            driver.execute_script("window.history.go(-1)")

        return parsed_docs


class MCCrawler(Crawler):
    """Crawler for the example web scraper"""
    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            **kwargs,
            pager=MCPager(
                starting_url=BASE_SOURCE_URL
            ),
            parser=MCParser()
        )


class FakeMCCrawler(Crawler):
    """Marine Corps crawler that just uses stubs and local source files"""
    def __init__(self, *args, **kwargs):
        with open(os.path.join(SOURCE_SAMPLE_DIR, "marine_pubs.html")) as f:
            default_text = f.read()

        super().__init__(
            *args,
            **kwargs,
            pager=MCPager(
                requestor=MapBasedPseudoRequestor(
                    default_text=default_text
                ),
                starting_url=BASE_SOURCE_URL
            ),
            parser=MCParser()
        )
