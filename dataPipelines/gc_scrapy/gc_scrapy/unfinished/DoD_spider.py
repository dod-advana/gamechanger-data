import scrapy
import re
import bs4
from dataPipelines.gc_scrapy.gc_scrapy.items import DocumentItem
from dataPipelines.gc_scrapy.gc_scrapy.data_model import Document, DownloadableItem

from dataPipelines.gc_scrapy.gc_scrapy.utils import abs_url


class DoDSpider(scrapy.Spider):
    name = 'DoD'

    start_urls = ['https://www.esd.whs.mil/DD/DoD-Issuances/DTM/']

    def parse(self, response):
        links = response.css('li.col-sm-6')[0].css('a')
        yield from response.follow_all(links[4:-1], self.parse_documents)

    def parse_documents(self, response):

        page_url = response.url

        # parse html response
        base_url = 'https://www.esd.whs.mil'
        soup = bs4.BeautifulSoup(response.body, features="html.parser")
        table = soup.find('table', attrs={'class': 'dnnGrid'})
        rows = table.find_all('tr')

        # set issuance type
        if page_url.endswith('dodd/'):
            doc_type = 'DoDD'
        elif page_url.endswith('dodi/'):
            doc_type = 'DoDI'
        elif page_url.endswith('dodm/'):
            doc_type = 'DoDM'
        elif page_url.endswith('inst/'):
            doc_type = 'AI'
        elif page_url.endswith('dtm/'):
            doc_type = 'DTM'
        else:
            doc_type = 'DoDI CPM'

        # iterate through each row of the table
        parsed_docs = []
        cac_required = ['CAC', 'PKI certificate required',
                        'placeholder', 'FOUO']
        for row in rows[1:]:

            # reset variables to ensure there is no carryover between rows
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

            # skip the extra rows, not included in the table
            try:
                row['class']  # all invalid rows do not have a class attribute
            except:
                continue

            # iterate through each cell of row
            for idx, cell in enumerate(row.find_all('td')):

                # remove unwanted characters
                data = re.sub(r'\s*[\n\t\r\s+]\s*', ' ', cell.text).strip()

                # set document variables based on current column
                if idx == 0:
                    pdf_url = abs_url(
                        base_url, cell.a['href']).replace(' ', '%20')
                    pdf_di = DownloadableItem(
                        doc_type='pdf',
                        web_url=pdf_url
                    )

                    # remove parenthesis from document name
                    data = re.sub(r'\(.*\)', '', data).strip()

                    # set doc_name and doc_num based on issuance
                    if page_url.endswith('dtm/'):
                        doc_name = data
                        doc_num = re.search(r'\d{2}.\d{3}', data)[0]
                    elif page_url.endswith('140025/'):
                        issuance_num = data.split()
                        doc_name = 'DoDI 1400.25 Volume ' + issuance_num[0] if issuance_num[0] != 'DoDI' \
                            else ' '.join(issuance_num).strip()

                        doc_num = issuance_num[0] if issuance_num[0] != 'DoDI' \
                            else issuance_num[-1]
                    else:
                        doc_name = data
                        doc_num = data.split(' ')[1] if data.find(
                            ' ') != -1 else data.split('-')[-1]

                elif idx == 1:
                    publication_date = data
                elif idx == 2:
                    doc_title = data
                elif idx == 3:
                    doc_name = doc_name + ' ' + data if data != '' else doc_name
                elif idx == 4:
                    chapter_date = data
                elif idx == 5:
                    exp_date = data

                # set boolean if CAC is required to view document
                cac_login_required = True if any(x in pdf_url for x in cac_required) \
                    or any(x in doc_title for x in cac_required) else False

            # all fields that will be used for versioning
            version_hash_fields = {
                # version metadata found on pdf links
                "item_currency": pdf_url.split('/')[-1],
                "exp_date": exp_date.strip(),
                "pub_date": publication_date.strip(),
                "chapter_date": chapter_date.strip()
            }
            doc = Document(
                doc_name=doc_name.strip(),
                doc_title=re.sub('\\"', '', doc_title),
                doc_num=doc_num.strip(),
                doc_type=doc_type.strip(),
                publication_date=publication_date,
                cac_login_required=cac_login_required,
                crawler_used="dod_issuances",
                source_page_url=page_url.strip(),
                version_hash_raw_data=version_hash_fields,
                downloadable_items=[pdf_di]
            )
            # doc = DocumentItem()
            # doc['doc_name']=doc_name.strip()
            # doc['doc_title']=re.sub('\\"', '', doc_title)
            # doc['doc_num']=doc_num.strip()
            # doc['doc_type']=doc_type.strip()
            # doc['publication_date']=publication_date
            # doc['cac_login_required']=cac_login_required
            # doc['crawler_used']="dod_issuances"
            # doc['source_page_url']=page_url.strip()
            # doc['version_hash_raw_data']=version_hash_fields
            # doc['downloadable_items']=[pdf_di]
            item = doc.to_item()
            # print(doc['source_page_url'])
            yield item
