import bs4
import os
from typing import Iterable, Tuple

from dataPipelines.gc_crawler.requestors import MapBasedPseudoRequestor
from dataPipelines.gc_crawler.exec_model import Crawler, Parser, Pager
from dataPipelines.gc_crawler.data_model import Document, DownloadableItem
from pathlib import Path
from selenium.webdriver.support.ui import WebDriverWait  # for implicit and explict waits
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from dataPipelines.gc_crawler.utils import abs_url, close_driver_windows_and_quit

from . import SOURCE_SAMPLE_DIR, BASE_SOURCE_URL, driver

def is_cac_required(dist_stm: str):
    if dist_stm.startswith("A") or dist_stm.startswith("N"):
        # the distribution statement is distribution A or says Not Applicable so anyone can access the information
        return False
    else:
        # the distribution statement has more restrictions

        return True


class ArmyPager(Pager):

    """Pager for Army pubs crawler"""
    def iter_page_links(self) -> Iterable[str]:
        """Iterator for page links"""
        pass

    def iter_page_links_with_text(self) -> Iterable[Tuple[str, str]]:

        # open web client
        driver.get(self.starting_url)

        WebDriverWait(driver, 5).until(
            ec.presence_of_element_located((By.XPATH, "//*[@id='navbarDropdownMenuLink']")))

        html = driver.execute_script("return document.documentElement.outerHTML")
        soup = bs4.BeautifulSoup(html, features="html.parser")
        # get target column of list items

        publications_list = soup.find_all('li', attrs={'class': 'nav-item'})[2]
        # extract links
        links = [link for link in publications_list.find_all('a', attrs={"class": "dropdown-item"})]

        # these links are not in the proper format to be scraped
        do_not_process = ["/ProductMaps/PubForm/PB.aspx", "/Publications/Administrative/POG/AllPogs.aspx"]

        html_list = []
        #last 6 create duplicate entries of previous scrapes
        for link in links[:-6]:
            if link['href'] == "#" or link['href'] in do_not_process:
                continue
            if not link['href'].startswith('http'):
                url = self.starting_url + link['href']
            else:
                url = link['href']
            driver.get(url)
            WebDriverWait(driver, 5).until(
                ec.presence_of_element_located((By.XPATH, "//*[@id='navbarDropdownMenuLink']")))
            html = driver.execute_script("return document.documentElement.outerHTML")
            html_list.append((driver.current_url, html))
            yield html_list[-1]





class ArmyParser(Parser):
    """Parser for Army Publication crawler"""

    def parse_docs_from_page(self, page_url: str, page_text: str) -> Iterable[Document]:
        """Parse document objects from page of text"""

        """Iterator for page links"""
        base_url = 'https://armypubs.army.mil'
        pub_url = base_url + '/ProductMaps/PubForm/'
        soup = bs4.BeautifulSoup(page_text, features="html.parser")
        table = soup.find('table', attrs={'class': 'gridview'})
        pub_links = table.find_all('a')
        info_pages = []
        for link in pub_links:
            info_url = pub_url + link['href']
            info_pages.append(info_url)

        parsed_docs = []
        for link in info_pages:
            try:
                driver.get(link)
                WebDriverWait(driver, 5).until(
                    ec.presence_of_element_located((By.XPATH, "//*[@id='navbarDropdownMenuLink']")))
            except TimeoutException:
                # reload once if the page fails to load again skip
                try:
                    driver.get(link)
                    WebDriverWait(driver, 5).until(
                        ec.presence_of_element_located((By.XPATH, "//*[@id='navbarDropdownMenuLink']")))
                except TimeoutException:
                    continue

            html = driver.execute_script("return document.documentElement.outerHTML")
            info_soup = bs4.BeautifulSoup(html, features="html.parser")
            rows = info_soup.find_all('tr')
            doc_name = rows[0].find_all('td')[1].text
            doc_title = rows[2].find_all('td')[1].text
            doc_num = rows[0].find_all('td')[1].text.split()[-1]
            doc_type = rows[0].find_all('td')[1].text.split()[0]
            publication_date = rows[1].find_all('td')[1].text
            cac_login_required = is_cac_required(rows[14].find_all('td')[1].text)
            linked_items = rows[3].find_all('td')[1].find_all('a')
            downloadable_items = []
            if not linked_items:
                # skip over the publication
                continue
            else:
                for item in linked_items:
                    if "PDF" in item.text and Path(rows[3].find_all('td')[1].find('a')['href']).suffix == ".pdf":
                        pdf_di = DownloadableItem(
                            doc_type='pdf',
                            web_url=abs_url(base_url, rows[3].find_all('td')[1].find('a')['href']).replace(' ', '%20')
                         )
                        downloadable_items.append(pdf_di)
            if not downloadable_items:
                continue
            version_hash_fields = {
                "pub_date": rows[1].find_all('td')[1].text,
                "pub_pin": rows[5].find_all('td')[1].text,
                "pub_status": rows[7].find_all('td')[1].text,
                "product_status": rows[8].find_all('td')[1].text,
                "replaced_info": rows[11].find_all('td')[1].text
            }
            doc = Document(
                doc_name=doc_name.strip(),
                doc_title=doc_title.strip(),
                doc_num=doc_num.strip(),
                doc_type=doc_type.strip(),
                publication_date=publication_date,
                cac_login_required=cac_login_required,
                crawler_used="army_pubs",
                source_page_url=link.strip(),
                version_hash_raw_data=version_hash_fields,
                downloadable_items=downloadable_items
            )

            parsed_docs.append(doc)

        return parsed_docs


class ArmyCrawler(Crawler):
    """Crawler for the example web scraper"""
    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            **kwargs,
            pager=ArmyPager(
                starting_url=BASE_SOURCE_URL
            ),
            parser=ArmyParser()
        )


class FakeArmyCrawler(Crawler):
    """Army Publication crawler that just uses stubs and local source files"""
    def __init__(self, *args, **kwargs):
        with open(os.path.join(SOURCE_SAMPLE_DIR, 'army_pubs.html')) as f:
            default_text = f.read()

        super().__init__(
            *args,
            **kwargs,
            pager=ArmyPager(
                requestor=MapBasedPseudoRequestor(
                    default_text=default_text
                ),
                starting_url=BASE_SOURCE_URL
            ),
            parser=ArmyParser()
        )
