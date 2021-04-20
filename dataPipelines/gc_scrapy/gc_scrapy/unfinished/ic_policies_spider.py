import scrapy
import re
import bs4
from ..items import DocumentItem
from ..data_model import Document, DownloadableItem
from ..utils import abs_url


class IcPoliciesSpider(scrapy.Spider):
    name = 'ic_policies'

    start_urls = ['https://www.dni.gov/index.php/what-we-do/ic-policies-reports/']

    def parse(self, response):
        base_url = 'https://www.dni.gov'
        links = response.css('div[itemprop="articleBody"]').css('ul')[0].css('li')[:-1]
        full_links = [base_url + l.css('a::attr(href)').get() for l in links]
        yield from response.follow_all(full_links, self.parse_documents)

    def parse_documents(self, response):

        """Parse document objects from page of text"""
        page_url = response.url
        # parse html response
        base_url = 'https://www.dni.gov'
        soup = bs4.BeautifulSoup(response.body, features="html.parser")
        div = soup.find('div', attrs={'itemprop': 'articleBody'})
        pub_list = div.find_all('p')

        # set policy type
        if page_url.endswith('directives'):
            doc_type = 'ICD'
        elif page_url.endswith('guidance'):
            doc_type = 'ICPG'
        elif page_url.endswith('memorandums'):
            doc_type = 'ICPM'
        else:
            doc_type = 'ICLR'

        # iterate through each publication
        cac_required = ['CAC', 'PKI certificate required', 'placeholder', 'FOUO']
        for row in pub_list:

            # skip empty rows
            if row.a is None:
                continue

            data = re.sub(r'\u00a0', ' ', row.text)
            link = row.a['href']

            # patterns to match
            name_pattern = re.compile(r'^[A-Z]*\s\d*.\d*.\d*.\d*\s')

            parsed_text = re.findall(name_pattern, data)[0]
            parsed_name = parsed_text.split(' ')
            doc_name = ' '.join(parsed_name[:2])
            doc_num = parsed_name[1]
            doc_title = re.sub(parsed_text, '', data)

            pdf_url = abs_url(base_url, link)
            pdf_di = DownloadableItem(
                doc_type='pdf',
                web_url=pdf_url
            )

            # extract publication date from the pdf url
            matches = re.findall(r'\((.+)\)', pdf_url.replace('%20', '-'))
            publication_date = matches[-1] if len(matches) > 0 else None

            # set boolean if CAC is required to view document
            cac_login_required = True if any(x in pdf_url for x in cac_required) \
                                         or any(x in doc_title for x in cac_required) else False

            # all fields that will be used for versioning
            version_hash_fields = {
                "item_currency": publication_date  # version metadata found on pdf links
            }

            doc = Document(
                doc_name=doc_name.strip(),
                doc_title=doc_title,
                doc_num=doc_num,
                doc_type=doc_type,
                publication_date=publication_date,
                cac_login_required=cac_login_required,
                crawler_used="ic_policies",
                source_page_url=page_url.strip(),
                version_hash_raw_data=version_hash_fields,
                downloadable_items=[pdf_di]
            )

            item = doc.to_item()
            yield item
