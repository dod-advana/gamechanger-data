from typing import List
import bs4
import re
from typing import Iterable

from dataPipelines.gc_crawler.requestors import (
    FileBasedPseudoRequestor,
    DefaultRequestor,
)
from dataPipelines.gc_crawler.exec_model import Crawler, Parser, Pager
from dataPipelines.gc_crawler.data_model import Document, DownloadableItem
from dataPipelines.gc_crawler.utils import abs_url

from . import SOURCE_SAMPLE_DIR, BASE_SOURCE_URL


class ExamplePager(Pager):
    """Pager for Example crawler"""

    def iter_page_links(self) -> Iterable[str]:
        """Iterator for page links"""
        for sample_file in 'page_1.html', 'page_2.html':
            yield self.starting_url + "/" + sample_file


class ExampleParser(Parser):
    """Parser for Example crawler"""

    def parse_docs_from_page(self, page_url: str, page_text: str) -> Iterable[Document]:
        """Parse document objects from page of text"""
        soup = bs4.BeautifulSoup(page_text, features="lxml")
        download_item_divs = soup.select(
            'div.main-content > div.downloads > div.download-item'
        )

        parsed_docs = []

        for div in download_item_divs:
            # general pub and versioning info
            title = div.select_one("div.download-title").text.strip()
            pub_date = div.select_one("div.download-pub-date").text.strip()
            # all fields that will be used for versioning
            version_hash_fields = {'pub_date': pub_date}

            # gathering downloadable items' info
            download_links_div = div.select_one('div.download-links')
            download_items: List[DownloadableItem] = []
            for pub_type, pattern in [('pdf', r'\bPDF\b'), ('xml', r'\bXML\b')]:
                a_tag = download_links_div.find(
                    name='a', text=re.compile(pattern=pattern, flags=re.IGNORECASE)
                )

                download_url: str = ""
                if a_tag:
                    download_url = abs_url(page_url, a_tag.attrs['href'])
                else:
                    continue

                actual_download_file_type_matcher = re.match(
                    r".*[.](\w+)$", download_url
                )

                actual_download_file_type = (
                    actual_download_file_type_matcher.group(1)
                    if actual_download_file_type_matcher
                    else None
                )

                download_items.append(
                    DownloadableItem(
                        doc_type=pub_type,
                        web_url=download_url,
                        compression_type=(
                            actual_download_file_type
                            if (actual_download_file_type or '').lower() != pub_type
                            else None
                        ),
                    )
                )

            # generate final document object
            doc = Document(
                doc_name=title,
                doc_title=title,
                doc_num="1",
                doc_type="example",
                source_page_url=page_url,
                publication_date=None,
                cac_login_required=False,
                version_hash_raw_data=version_hash_fields,
                downloadable_items=download_items,
                crawler_used="example"
            )

            parsed_docs.append(doc)

        return parsed_docs


class ExampleCrawler(Crawler):
    """Crawler for the example web scraper"""

    def __init__(self, starting_url: str = "http://localhost:8000"):
        pager = ExamplePager(starting_url=starting_url)
        super().__init__(pager=pager, parser=ExampleParser())


class FakeExampleCrawler(Crawler):
    """Example crawler that just uses local source files"""

    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            **kwargs,
            pager=ExamplePager(
                requestor=FileBasedPseudoRequestor(
                    fake_web_base_url=BASE_SOURCE_URL,
                    source_sample_dir_path=SOURCE_SAMPLE_DIR,
                ),
                starting_url=BASE_SOURCE_URL,
            ),
            parser=ExampleParser(),
        )
