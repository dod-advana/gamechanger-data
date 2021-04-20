# -*- coding: utf-8 -*-
import scrapy
from urllib.parse import urljoin
from dataPipelines.gc_scrapy.gc_scrapy.items import DocItem
from dataPipelines.gc_scrapy.gc_scrapy.GCSpider import GCSpider


class BupersSpider(GCSpider):
    name = "Bupers_Crawler"
    allowed_domains = ['mynavyhr.navy.mil']
    start_urls = [
        "https://www.mynavyhr.navy.mil/References/Instructions/BUPERS-Instructions/"
    ]

    doc_type = "BUPERSINST"
    cac_login_required = False

    @staticmethod
    def clean(text):
        return text.replace('\xa0', ' ').encode('ascii', 'ignore').decode('ascii').strip()

    @staticmethod
    def filter_empty(text_list):
        return list(filter(lambda a: a, text_list))

    @staticmethod
    def get_file_type(url):
        file_url, _, _ = url.partition('?ver=')
        _, _, extension = file_url.rpartition('.')
        return extension.lower()

    def parse(self, response):
        # first 3 rows are what should be header content but are just regular rows, so nth-child used
        rows = response.css("div.livehtml > table > tbody tr:nth-child(n + 4)")

        for row in rows:
            links_raw = row.css('td:nth-child(1) a::attr(href)').getall()
            if not len(links_raw):
                # skip rows without anchor, no downloadable docs
                continue

            # data is nested in a variety of ways, lots of checks :/
            doc_nums_raw = []
            for selector in ['a strong::text', 'a::text', 'span::text', 'font::text']:
                nums = row.css(f'td:nth-child(1) {selector}').getall()
                if nums is not None:
                    doc_nums_raw += nums

            doc_titles_raw = []
            for selector in ['strong::text', 'span::text', 'font::text']:
                titles = row.css(f'td:nth-child(2) {selector}').getall()
                if titles is not None:
                    doc_titles_raw += titles

            dates_raw = []
            for selector in ['strong::text', 'span::text', 'font::text']:
                dates = row.css(f'td:nth-child(3) {selector}').getall()
                if titles is not None:
                    dates_raw += dates

            # clean unicode and filter empty strings after
            doc_nums_cleaned = self.filter_empty(
                [self.clean(text) for text in doc_nums_raw])
            doc_title = " ".join(self.filter_empty(
                [self.clean(text) for text in doc_titles_raw]))
            dates_cleaned = self.filter_empty(
                [self.clean(text) for text in dates_raw])
            links_cleaned = self.filter_empty(links_raw)

            # happy path, equal num of docs, links, dates
            if ((len(doc_nums_cleaned) == len(links_cleaned) == len(dates_cleaned))
                    or (len(dates_cleaned) > len(doc_nums_cleaned))) \
                    and (not 'CH-1' in doc_nums_cleaned):
                # some doc nums arent downloadable but have dates
                # special case for equal num but should be a combined doc num with CH-1

                for i in range(len(doc_nums_cleaned)):
                    doc_num = doc_nums_cleaned[i]
                    href = links_cleaned[i]
                    file_type = self.get_file_type(href)

                    web_url = urljoin(
                        self.start_urls[0], href).replace(' ', '%20')
                    downloadable_items = [
                        {
                            "doc_type": file_type,
                            "web_url": web_url,
                            "compression_type": None
                        }
                    ]

                    version_hash_fields = {
                        "item_currency": href.replace(' ', '%20'),
                        "document_title": doc_title,
                        "document_number": doc_num
                    }

                    yield DocItem(
                        doc_name=f"{self.doc_type} {doc_num}",
                        doc_title=doc_title,
                        doc_num=doc_num,
                        publication_date=dates_cleaned[i],
                        downloadable_items=downloadable_items,
                        version_hash_raw_data=version_hash_fields,
                    )

            # doc num was split, combine them into one string
            elif (len(doc_nums_cleaned) > len(dates_cleaned) and len(links_cleaned) == len(dates_cleaned)) \
                    or (any(item in ['Vol 1', 'Vol 2', 'CH-1'] for item in doc_nums_cleaned)):
                # special cases for spit names of same doc

                doc_num = " ".join(doc_nums_cleaned)

                href = links_cleaned[0]
                file_type = self.get_file_type(href)

                web_url = urljoin(self.start_urls[0], href).replace(' ', '%20')
                downloadable_items = [
                    {
                        "doc_type": file_type,
                        "web_url": web_url,
                        "compression_type": None
                    }
                ]

                version_hash_fields = {
                    "item_currency": href,
                    "document_title": doc_title,
                    "document_number": doc_num
                }

                yield DocItem(
                    doc_name=f"{self.doc_type} {doc_num}",
                    doc_title=doc_title,
                    doc_num=doc_num,
                    publication_date=dates_cleaned[0],
                    downloadable_items=downloadable_items,
                    version_hash_raw_data=version_hash_fields,
                )

            # there are supplemental downloadable items
            elif len(links_cleaned) > len(dates_cleaned):
                doc_num = doc_nums_cleaned[0]

                downloadable_items = []

                for href in links_cleaned:
                    file_type = self.get_file_type(href)
                    web_url = urljoin(
                        self.start_urls[0], href).replace(' ', '%20')
                    downloadable_items.append(
                        {
                            "doc_type": file_type,
                            "web_url": web_url,
                            "compression_type": None
                        }
                    )

                version_hash_fields = {
                    "item_currency": links_cleaned[0],
                    "document_title": doc_title,
                    "document_number": doc_num
                }

                yield DocItem(
                    doc_name=f"{self.doc_type} {doc_num}",
                    doc_title=doc_title,
                    doc_num=doc_num,
                    publication_date=dates_cleaned[0],
                    downloadable_items=downloadable_items,
                    version_hash_raw_data=version_hash_fields,
                )
            else:
                raise Exception(
                    'Row data not captured, doesnt match known cases', row)
