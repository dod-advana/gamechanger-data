import scrapy
import re
import bs4
from ..items import DocumentItem
from ..data_model import Document, DownloadableItem
from ..utils import abs_url
from re import search


class JcsPubsSpider(scrapy.Spider):
    name = 'jcs_pubs'

    start_urls = ['https://www.jcs.mil']

    def parse(self, response):
        links = response.css('ul.dropdown-menu')[3].css('li')[1:-1]
        full_links = [l.css('a::attr(href)').get() for l in links]
        yield from response.follow_all(full_links, self.parse_pager)

    def parse_pager(self,response):
        page_url = response.url
        next_page_links = response.css('table.dnnFormItem')[1].css('a::attr(href)')
        pages = [page_url]
        if len(next_page_links) > 0:
            page_ext = next_page_links[-1].get()[:-1]
            num_pages = next_page_links[-1].get()[-1]
            for i in range(1,int(num_pages)):
                pages.append(page_url + page_ext + str(i))
        yield from response.follow_all(pages, self.parse_documents)

    def parse_documents(self, response):

        page_url = response.url
        #
        # # parse html response
        # base_url = 'https://www.esd.whs.mil'
        # soup = bs4.BeautifulSoup(response.body, features="html.parser")
        # table = soup.find('table', attrs={'class': 'dnnGrid'})
        # rows = table.find_all('tr')

        # parse html response
        #encoded_str = page_text.encode('ascii', 'ignore')
        soup = bs4.BeautifulSoup(response.body, features="html.parser")
        tables = soup.find_all('table', attrs={'class': 'dnnFormItem'})
        rows = tables[0].tbody.find_all('tr')

        # set document type
        if search('Instructions', page_url):
            doc_type = 'CJCSI'
        elif search('Manuals', page_url):
            doc_type = 'CJCSM'
        elif search('Notices', page_url):
            doc_type = 'CJCSN'
        else:
            doc_type = 'CJCS GDE'

        # iterate through each row of the table
        cac_required = ['CAC', 'PKI certificate required', 'placeholder', 'FOUO']
        for row in rows[1:]:

            # reset variables to ensure there is no carryover between rows
            doc_num = ''
            doc_name = ''
            doc_title = ''
            publication_date = ''
            cac_login_required = False
            pdf_url = ''
            pdf_di = None

            pdf_url = row.td.a['href'].strip()
            doc_name = row.td.a.text.strip()

            doc_num_matcher = re.match(r"(?P<doc_type>(\s*\w+)*?)\s+(?P<doc_num>([0-9]+[a-zA-Z0-9.-_]*)+)", doc_name)
            if doc_num_matcher:
                doc_num = doc_num_matcher.groupdict()['doc_num']
            else:
                doc_num = doc_name.split(' ')[-1]

            doc_title = row.find('td', attrs={'class': 'DocTitle'}).text.strip()
            publication_date = row.find('td', attrs={'class': 'DocDateCol'}).text.strip()

            pdf_di = DownloadableItem(
                doc_type='pdf',
                web_url=self.start_urls[0] + pdf_url
            )

            # set boolean if CAC is required to view document
            cac_login_required = True if any(x in pdf_url for x in cac_required) \
                                         or any(x in doc_title for x in cac_required) else False

            # all fields that will be used for versioning
            version_hash_fields = {
                "item_currency": row.find('td', attrs={'class': 'CurrentCol'}).text.strip(),
                "pub_description": re.sub('\\"', '', row.find('td', attrs={'class': 'DocInfoCol'}).img['title'].strip())
            }

            doc = Document(
                doc_name=doc_name.strip(),
                doc_title=re.sub('\\"', '', doc_title),
                doc_num=doc_num.strip(),
                doc_type=doc_type.strip(),
                publication_date=publication_date,
                cac_login_required=cac_login_required,
                crawler_used="jcs_pubs",
                source_page_url=page_url.strip(),
                version_hash_raw_data=version_hash_fields,
                downloadable_items=[pdf_di]
            )

            item = doc.to_item()
            yield item