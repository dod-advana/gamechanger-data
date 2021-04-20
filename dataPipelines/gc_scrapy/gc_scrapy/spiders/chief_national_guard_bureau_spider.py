import scrapy
from datetime import datetime
import re
from urllib.parse import urljoin
from dataPipelines.gc_scrapy.gc_scrapy.items import DocItem
from dataPipelines.gc_scrapy.gc_scrapy.GCSpider import GCSpider


class CNGBISpider(GCSpider):
    name = "Chief_National_Guard_Bureau_Instructions"
    allowed_domains = ['ngbpmc.ng.mil']
    start_urls = [
        'https://www.ngbpmc.ng.mil/publications1/cngbi/'
    ]

    file_type = "pdf"
    doc_type = "CNGBI"
    cac_login_required = False

    @staticmethod
    def clean(text):
        return text.encode('ascii', 'ignore').decode('ascii').strip()

    @staticmethod
    def get_file_type(url):
        file_url, _, _ = url.partition('?')
        _, _, extension = file_url.rpartition('.')
        return extension.lower()

    def parse(self, response):
        rows = response.css('div.WordSection1 table.MsoNormalTable tbody tr')

        for row in rows:
            href_raw: str = row.css('td:nth-child(1) a::attr(href)').get()
            if href_raw.startswith('/'):
                web_url = urljoin(self.start_urls[0], href_raw)
            else:
                web_url = href_raw

            file_type = self.get_file_type(web_url)

            downloadable_items = [
                {
                    "doc_type": file_type,
                    "web_url": web_url.replace(' ', '%20'),
                    "compression_type": None
                }
            ]

            doc_name_raw = row.css('td:nth-child(1) a span::text').get()
            doc_num_raw = doc_name_raw.replace('CNGBI ', '')

            publication_date = row.css('td:nth-child(2) span::text').get()

            doc_title_raw = row.css('td:nth-child(3) a::text').get()
            if doc_title_raw is None:
                doc_title_raw = row.css('td:nth-child(3) span::text').get()

            doc_title = self.clean(doc_title_raw)

            version_hash_fields = {
                "item_currency": href_raw.replace(' ', '%20'),
                "document_title": doc_title,
                "document_number": doc_num_raw
            }

            yield DocItem(
                doc_name=doc_name_raw,
                doc_title=doc_title,
                doc_num=doc_num_raw,
                publication_date=publication_date,
                # cac_login_required=False,
                downloadable_items=downloadable_items,
                version_hash_raw_data=version_hash_fields,
            )
