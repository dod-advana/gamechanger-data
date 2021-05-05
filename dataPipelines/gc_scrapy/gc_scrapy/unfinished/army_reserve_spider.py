import scrapy
import re
from urllib.parse import urljoin, urlencode, parse_qs
from dataPipelines.gc_scrapy.gc_scrapy.items import DocItem
from dataPipelines.gc_scrapy.gc_scrapy.GCSpider import GCSpider

type_and_num_regex = re.compile(r"([a-zA-Z].*) (\d.*)")


class ArmyReserveSpider(GCSpider):
    name = "Army_Reserve"
    allowed_domains = ['usar.army.mil']
    start_urls = [
        'https://www.usar.army.mil/Publications/'
    ]

    file_type = "pdf"
    cac_login_required = False

    section_selector = "div.DnnModule.DnnModule-ICGModulesExpandableTextHtml div.Normal"

    @staticmethod
    def clean(text):
        return text.encode('ascii', 'ignore').decode('ascii').strip()

    def parse(self, response):

        selected_items = response.css(
            "div.DnnModule.DnnModule-ICGModulesExpandableTextHtml div.Normal > div p")
        for item in selected_items:

            pdf_url = item.css('a::attr(href)').get()
            if pdf_url is None:
                continue

            # join relative urls to base
            web_url = urljoin(self.start_urls[0], pdf_url) if pdf_url.startswith(
                '/') else pdf_url
            # encode spaces from pdf names
            web_url = web_url.replace(" ", "%20")

            cac_login_required = True if "usar.dod.afpims.mil" in web_url else False

            downloadable_items = [
                {
                    "doc_type": self.file_type,
                    "web_url": web_url,
                    "compression_type": None
                }
            ]
            doc_name_raw = item.css('strong::text').get()
            doc_title_raw = item.css('a::text').get()
            # some are nested in span
            if doc_title_raw is None:
                doc_title_raw = item.css('a span::text').get()
                # some dont have anything except the name e.g. FY20 USAR IDT TRP Policy Update
                if doc_title_raw is None:
                    doc_title_raw = doc_name_raw

            doc_name = self.clean(doc_name_raw)
            doc_title = self.clean(doc_title_raw)

            type_and_num_groups = re.search(type_and_num_regex, doc_name)
            if type_and_num_groups is not None:
                doc_type = type_and_num_groups[1]
                doc_num = type_and_num_groups[2]
            else:
                doc_type = "USAR Document"
                doc_num = ""

            version_hash_fields = {
                # version metadata found on pdf links
                "item_currency": web_url.split('/')[-1],
                "document_title": doc_title,
                "document_number": doc_num
            }

            yield DocItem(
                doc_name=doc_name,
                doc_title=doc_title,
                doc_num=doc_num,
                doc_type=doc_type,
                cac_login_required=cac_login_required,
                downloadable_items=downloadable_items,
                version_hash_raw_data=version_hash_fields,
            )
