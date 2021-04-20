import scrapy
import re
import bs4
from ..items import DocumentItem
from ..data_model import Document, DownloadableItem
from ..utils import abs_url
from ..exceptions import ParsingError


class USCodeSpider(scrapy.Spider):
    name = 'us_code'

    start_urls = ['https://uscode.house.gov/download/download.shtml']

    def parse(self, response):
        page_url = response.url
        soup = bs4.BeautifulSoup(response.body, features="lxml")
        usc_item_divs = soup.select('div.uscitemlist > div.uscitem')

        parsed_docs = []

        for item_idx, item_div in enumerate(usc_item_divs):

            title_class_regex = re.compile(r"^usctitle.*$")

            title_div = item_div.find('div', attrs={'class': title_class_regex})
            currency_div = item_div.select_one('div.itemcurrency')
            download_div = item_div.select_one('div.itemdownloadlinks')

            # skip all-titles item
            if title_div.get('id') == 'alltitles':
                continue

            # TODO: Find correct logic to automate including Title 53 when it eventually gets published
            # skip reserved pub
            if title_div.get("id") == 'us/usc/t53':
                continue

            # DOC & DOWNLOAD INFO
            doc_name = re.sub(r'[^0-9a-zA-Z _-]+', '', title_div.text).strip()

            # Construct better doc_name for appendices than just "Appendix"
            if 'usctitleappendix' in title_div.get('class'):
                # we should never have appendices without preceding titles
                if item_idx == 0:
                    continue

                previous_item_div = usc_item_divs[item_idx - 1]

                previous_title_name_matcher = re.match(
                    r"^.*\b(Title\s+\d+).*$",
                    previous_item_div.text,
                    flags=(re.IGNORECASE | re.DOTALL),
                )

                if previous_title_name_matcher:
                    previous_title_name_abbreviated = previous_title_name_matcher.group(
                        1
                    )
                else:
                    raise ParsingError(
                        "Could not find appropriate US Code title corresponding to given Appendix"
                    )

                new_doc_name = "{0} - {1}".format(
                    previous_title_name_abbreviated, doc_name
                )
                doc_name = new_doc_name

            # DOCUMENT NUMBER
            doc_name_matcher = re.match(
                r"^.*(\bTitle\b)\s+(\d+)[^a-zA-Z]*(.*)$", doc_name, flags=re.IGNORECASE
            )

            if doc_name_matcher:
                doc_num = doc_name_matcher.group(2)
                doc_title = doc_name_matcher.group(3)
            else:
                raise ParsingError("Could not parse doc_name appropriately")

            # DOWNLOAD INFO
            pdf_url = abs_url(
                page_url,
                download_div.find(
                    name='a', text=re.compile(pattern=r'\[PDF\]', flags=re.IGNORECASE)
                ).attrs['href'],
            )

            xml_url = abs_url(
                page_url,
                download_div.find(
                    name='a', text=re.compile(pattern=r'\[XML\]', flags=re.IGNORECASE)
                ).attrs['href'],
            )

            # CURRENCY INFO
            item_currency = currency_div.text.strip() or None

            # For cases where there's nothing inside currency_div
            if not item_currency:
                url_pattern = re.compile(
                    pattern=r"""
                                        (?P<url_base>.*/)
                                        (?P<file_name>
                                                (?P<pub_id>\w+)
                                                @
                                                (?P<item_currency>\d+[a-zA-Z]?-\d+[a-zA-Z]?)
                                                [.]
                                                (?P<file_ext>\w+)
                                        )
                                    """,
                    flags=re.VERBOSE,
                )

                match = url_pattern.match(pdf_url)
                item_currency = (
                    match.groupdict().get("item_currency") if match else None
                )

            # all fields that will be used for versioning
            version_hash_fields = {'item_currency': item_currency}

            # setup downloadable items to make sure all fields are there
            pdf_di = DownloadableItem(
                doc_type='pdf', web_url=pdf_url, compression_type="zip"
            )

            xml_di = DownloadableItem(
                doc_type='xml', web_url=xml_url, compression_type="zip"
            )

            # generate final document object
            doc = Document(
                doc_name=doc_name,
                doc_title=doc_title,
                doc_num=doc_num,
                doc_type="Title",
                publication_date=None,
                cac_login_required=False,
                crawler_used="us_code",
                source_page_url=page_url,
                version_hash_raw_data=version_hash_fields,
                downloadable_items=[pdf_di, xml_di],
            )

            doc_item = doc.to_item()
            yield doc_item

