import scrapy
import re
import bs4
from ..items import DocumentItem
from ..data_model import Document, DownloadableItem
from ..utils import abs_url


class OpmSpider(scrapy.Spider):
    name = 'opm'

    start_urls = ['https://www.whitehouse.gov/omb/information-for-agencies/memoranda/']

    def parse(self, response):
        page_url = response.url
        base_url = 'https://www.whitehouse.gov'

        soup = bs4.BeautifulSoup(response.body, features="html.parser")

        parsed_nums = []

        # get target column of list items
        parsed_docs = []
        li_list = soup.find_all('li')
        for li in li_list:
            doc_type = 'OMBM'
            doc_num = ''
            doc_name = ''
            doc_title = ''
            chapter_date = ''
            publication_date = ''
            cac_login_required = False
            pdf_url = ''
            exp_date = ''
            issuance_num = ''
            pdf_di = None
            if 'supersede' not in li.text.lower():
                a_list = li.findChildren('a')
                for a in a_list:
                    href = 'href'
                    if a.get('href') is None:
                        href = 'data-copy-href'
                    if a[href].lower().endswith('.pdf'):
                        if a[href].startswith('http'):
                            pdf_url = a[href]
                        else:
                            pdf_url = base_url + a[href].strip()
                    commaTokens = a.text.strip().split(',', 1)
                    spaceTokens = a.text.strip().split(' ', 1)
                    if len(commaTokens) > 1 and len(commaTokens[0]) < len(spaceTokens[0]):
                        doc_num = commaTokens[0]
                        doc_title = re.sub(r'^.*?,', '', a.text.strip())
                        doc_name = "OMBM " + doc_num
                    elif len(spaceTokens) > 1 and len(spaceTokens[0]) < len(commaTokens[0]):
                        doc_num = spaceTokens[0].rstrip(',.*')
                        doc_title = spaceTokens[1]
                        doc_name = "OMBM " + doc_num
                    possible_date = li.text[li.text.find("(") + 1:li.text.find(")")]
                    if re.match(pattern=r".*, \d{4}.*", string=possible_date):
                        publication_date = possible_date
                if pdf_url != '' and doc_num.count('-') == 2:
                    pdf_di = DownloadableItem(
                        doc_type='pdf',
                        web_url=pdf_url
                    )
                    version_hash_fields = {
                        "item_currency": pdf_url.split('/')[-1],  # version metadata found on pdf links
                        "pub_date": publication_date.strip(),
                    }
                    parsed_title = re.sub('\\"', '', doc_title)
                    parsed_num = doc_num.strip()
                    if parsed_num not in parsed_nums:
                        doc = Document(
                            doc_name=doc_name.strip(),
                            doc_title=parsed_title,
                            doc_num=parsed_num,
                            doc_type=doc_type.strip(),
                            publication_date=publication_date,
                            cac_login_required=cac_login_required,
                            crawler_used="opm_pubs",
                            source_page_url=page_url.strip(),
                            version_hash_raw_data=version_hash_fields,
                            downloadable_items=[pdf_di]
                        )
                        parsed_docs.append(doc)
                        parsed_nums.append(parsed_num)
                        doc_item = doc.to_item()
                        yield doc_item
