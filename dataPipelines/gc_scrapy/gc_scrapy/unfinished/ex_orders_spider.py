import scrapy
import re
import bs4
from ..items import DocumentItem
from ..data_model import Document, DownloadableItem
from ..utils import abs_url
import json
import datetime


class ExOrdersSpider(scrapy.Spider):
    name = 'ex_orders'

    start_urls = ['https://www.federalregister.gov/presidential-documents/executive-orders']

    def parse(self, response):

        link = response.css('span.links')[0].css('a')
        yield response.follow(link[1], self.parse_documents)


    def parse_documents(self, response):

        parsed = json.loads(response.text)

        parsed_docs = []
        for execOrder in parsed["results"]:

            # DOWNLOAD INFO
            if execOrder["pdf_url"]:
                pdf_di = DownloadableItem(doc_type='pdf', web_url=execOrder["pdf_url"])
            else:
                pass

            if execOrder["full_text_xml_url"]:
                xml_di = DownloadableItem(
                    doc_type='xml', web_url=execOrder["full_text_xml_url"]
                )
            else:
                pass

            # derive EO Number from context
            if execOrder["executive_order_number"] is None:
                execOrder["executive_order_number"] = str(int(parsed_docs[-1].doc_num) - 1)

            # generate final document object
            doc = Document(
                doc_name="EO " + execOrder["executive_order_number"],
                doc_title=execOrder["title"],
                doc_num=execOrder["executive_order_number"],
                doc_type="EO",
                publication_date=execOrder["publication_date"],
                cac_login_required=False,
                crawler_used="ex_orders",
                source_page_url=execOrder["html_url"],
                version_hash_raw_data={
                    "item_currency": execOrder["publication_date"],
                    "version_hash": execOrder["document_number"],
                    "citation": execOrder["citation"],
                    "title": execOrder["title"],
                },
                access_timestamp="{:%Y-%m-%d %H:%M:%S.%f}".format(
                    datetime.datetime.now()
                ),
                source_fqdn="https://www.federalregister.gov",
                downloadable_items=[pdf_di, xml_di],
            )
            parsed_docs.append(doc)
            item = doc.to_item()
            yield item

        # return parsed_docs