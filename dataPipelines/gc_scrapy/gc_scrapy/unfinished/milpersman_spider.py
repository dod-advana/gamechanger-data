import scrapy
import re
import bs4
from dataPipelines.gc_scrapy.gc_scrapy.items import DocumentItem
from dataPipelines.gc_scrapy.gc_scrapy.data_model import Document, DownloadableItem
from dataPipelines.gc_scrapy.gc_scrapy.utils import abs_url


def remove_html_tags(text):
    import re
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)


class MilpersmanSpider(scrapy.Spider):
    name = 'milpersman'

    start_urls = ['https://www.public.navy.mil/bupers-npc/reference/milpersman/Pages/default.aspx']

    def parse(self, response):
        soup = bs4.BeautifulSoup(response.body, features="html.parser")
        meta = soup.find("li", {"class": "static selected"})
        link_list = meta.find_all("a")
        links = ["https://www.public.navy.mil" + link['href'] for link in link_list if
                 link['href'].endswith('Pages/default.aspx')]

        yield from response.follow_all(links[1:2], self.parse_pager)
        yield from response.follow_all(links[2:], self.parse_documents)

    def parse_pager(self, response):
        soup2 = bs4.BeautifulSoup(response.body, 'html.parser')

        meta = soup2.find("li", {"class": "static selected"})
        link_list = meta.find_all("a")
        links = ["https://www.public.navy.mil" + link['href'] for link in link_list if
                 link['href'].endswith('Pages/default.aspx')]
        print('\n\n\n\n')
        print(response.url)
        print(links)
        print('\n\n\n\n')
        if len(links) > 1:
            links = links[1:]
        yield from response.follow_all(links, self.parse_documents)

    def parse_documents(self, response):

        page_url = response.url
        doc_num = []
        pdf = []
        doc_title = []
        datelist = []
        doctype = []

        soup = bs4.BeautifulSoup(response.body, 'html.parser')
        webpart2 = soup.find("div", {"class": "pageContent"})
        meta = webpart2.find_all("tr")
        for row in meta[3:]:
            if ((remove_html_tags((str(row))).isspace()) or not remove_html_tags((str(row)))):
                continue
            for idx, cell in enumerate(row.find_all('td')):
                doc_type = "MILPERSMAN"
                if (idx == 0):
                    words = ''
                    links = cell.find_all("a")
                    link_list = list(links)
                    nums = []
                    pdf_links = ["https://www.public.navy.mil" + link['href'] for link in link_list if
                                 link['href'].endswith('pdf')]
                    if not pdf_links:
                        continue
                    if (len(pdf_links) > 1):
                        nums = []
                        doc_nums = remove_html_tags((str(cell))).lstrip(" ").rstrip(" ").split()
                        for i, value in enumerate(doc_nums):
                            if (str(value).startswith("CH-")):
                                nums.append(i)
                        for i in nums:
                            doc_nums[i - 1:i + 1] = ['-'.join(doc_nums[i - 1:i + 1])]
                        words = " ".join(doc_nums)
                    elif (len(pdf_links) == 1):
                        words = remove_html_tags((str(cell))).encode('ascii', 'ignore').decode('ascii').lstrip(
                            " ").rstrip(" ")
                        words = " ".join(words.split())
                        if ("BUPERS" in str(words.split()[0])):
                            doc_type = str(words.split()[0])
                            words = ' '.join(words.split()[1:])
                        if (len(words.split()) > 1):
                            if (str(words.split()[1]).startswith("CH-") or str(words.split()[1]).startswith("ch-")):
                                words = '-'.join(words.split()[0:2])
                            else:
                                words = words.split()[0]
                        if (len(words.split()) == 1):
                            pass
                    if (len(words.split()) == 1):
                        if (words in doc_num):
                            number_of_times = sum(1 for s in doc_num if words in s)
                            words = words + "-" + str(number_of_times)
                        doc_num.append(words)
                        pdf.append(str(pdf_links[0]))
                        doctype.append(doc_type)
                    elif (len(words.split()) > 1):
                        for word in words.split():
                            doc_num.append(str(word))
                            doctype.append(doc_type)
                    if (len(pdf_links) > 1):
                        for links in pdf_links:
                            pdf.append(links)
                if (idx == 1):
                    words = remove_html_tags((str(cell))).lstrip(" ").rstrip(" ")
                    words = " ".join(words.split()).encode('ascii', 'ignore').decode('ascii')
                    if (not list(words)):
                        continue
                    else:
                        words
                    if (len(pdf_links) > 1):
                        evalue = []
                        evalue = [words] * len(pdf_links)
                        doc_title.extend(evalue)
                    elif (len(pdf_links) == 1):
                        doc_title.append(words)
                if (idx == 2):
                    words = remove_html_tags((str(cell))).lstrip(" ").rstrip(" ")
                    words = " ".join(words.split()).encode('ascii', 'ignore').decode('ascii')
                    if (not list(words)):
                        continue
                    else:
                        list_word = words.split()
                        short = []
                        for ind, entry in enumerate(list_word):
                            if (len(str(entry)) < 8):
                                short.append(ind)
                        for i in short:
                            part1 = ' '.join(words.split()[:i + 1])
                            part2 = ' '.join(words.split()[i + 1:])
                            joined = part1 + part2
                            words = joined
                    if (len(pdf_links) > 1):
                        for ii in range(len(pdf_links)):
                            datelist.append(word.split()[len(word.split()) - ii - 1])
                    elif (len(pdf_links) == 1):
                        datelist.append(str(words.split()[-1]))
                    else:
                        pass

        final = list(zip(doctype, doc_num, doc_title, pdf))
        final = [list(x) for x in final]

        for item in final:
            dtype = item[0]
            dnum = item[1]
            dtitle = item[2]
            dname = dtype + " " + dnum
            cac_login_required = False
            publication_date = "N/A"
            url = item[3]
            pdf_di = DownloadableItem(doc_type='pdf', web_url=url)
            version_hash_fields = {
                "item_currency": str(url).split('/')[-1],  # version metadata found on pdf links
                "document_title": dtitle.strip(),
                "document_number": dnum.strip()
            }
            doc = Document(
                doc_name=dname.strip(),
                doc_title=re.sub('\\"', '', dtitle),
                doc_num=dnum.strip(),
                doc_type=dtype.strip(),
                publication_date=publication_date,
                cac_login_required=cac_login_required,
                crawler_used="milpersman_crawler",
                source_page_url=page_url.strip(),
                version_hash_raw_data=version_hash_fields,
                downloadable_items=[pdf_di]
            )
            doc_item = doc.to_item()
            yield doc_item
