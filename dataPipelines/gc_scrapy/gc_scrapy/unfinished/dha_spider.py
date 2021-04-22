import scrapy
from datetime import datetime
import re
from urllib.parse import urlparse
from dataPipelines.gc_scrapy.gc_scrapy.items import DocItem
from dataPipelines.gc_scrapy.gc_scrapy.GCSpider import GCSpider

doc_num_re = re.compile("[0-9]+[.-][0-9]+")


class DHASpider(GCSpider):
    name = "dha_pubs"
    allowed_domains = ['health.mil']
    start_urls = [
        'https://www.health.mil/About-MHS/OASDHA/Defense-Health-Agency/Administration-and-Management/DHA-Publications'
    ]

    file_type = "pdf"
    cac_login_required = False

    def parse(self, response):
        rows = response.css('table.dataTable tbody tr')

        docs_data = rows.css('a::text').getall()
        pdf_urls = [
            f"https://www.health.mil{href}" for href in rows.css('a::attr(href)').getall()
        ]
        publication_dates = rows.css('td.fd-col2::text').getall()

        for (doc_data, publication_date, pdf_url) in zip(docs_data, publication_dates, pdf_urls):
            doc_data = doc_data.split(':')

            if len(doc_data) == 1:  # if no colon then no doc number
                if doc_data[0] == "(DTM)-19-004 -Military Service by Transgender Persons and Persons with Gender Dysphoria (Change 1)":
                    doc_num = "19-004"
                    doc_name = "DTM"
                    doc_title = doc_data[0][14:]
                    version_hash_fields = {
                        "doc_name": 'DTM', "doc_title": doc_data[0][14:]}
                else:
                    doc_num = " "
                    doc_title = doc_data[0]
                    doc_name = doc_data[0]
                    version_hash_fields = {
                        "doc_name": doc_data[0], "doc_title": doc_data[0]}
            else:

                tmptitle = doc_data[1][1:].replace("\u201cClinical", "Clinical").replace(
                    "System,\u201d", "System").replace("BUILDER\u2122 ", "Builder").replace("\u2013", "")

                if "Volume" in tmptitle:
                    doc_num = doc_data[0][7:] + " Volume "+tmptitle.split()[-1]
                else:
                    doc_num = doc_data[0][7:]
                doc_title = (doc_data[1][1:].replace("\u201cClinical", "Clinical").replace(
                    "System,\u201d", "System").replace("BUILDER\u2122 ", "Builder").replace("\u2013", ""))
                doc_name = doc_data[0][:6]

                version_hash_fields = {
                    "doc_name": doc_data[0][:7], "doc_title": doc_data[1]}

            downloadable_items = [
                {
                    "doc_type": self.file_type,
                    "web_url": pdf_url,
                    "compression_type": None
                }
            ]

            yield DocItem(
                doc_name=doc_name.replace(" ", "-")+" "+doc_num,
                doc_title=doc_title,
                doc_num=doc_num,
                doc_type=doc_name.replace(" ", "-"),
                publication_date=publication_date,
                cac_login_required=False,
                downloadable_items=downloadable_items,
                version_hash_raw_data=version_hash_fields,
            )
