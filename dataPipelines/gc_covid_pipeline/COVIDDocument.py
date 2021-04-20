import json
from pathlib import Path
import multiprocessing
import datetime
from xhtml2pdf import pisa
from mako.template import Template
import re
import os
import csv
import html
from functools import partial
from weasyprint.fonts import FontConfiguration
import os.path
from os import path

from weasyprint import HTML, CSS

# this module's path
PACKAGE_PATH: str = os.path.dirname(os.path.abspath(__file__))


# font_path = os.path.join(PACKAGE_PATH, 'fonts/msyh.ttf')
# pdfmetrics.registerFont(TTFont('yh', font_path))
# DEFAULT_FONT['helvetica'] = 'yh'

class COVIDDocument:
    def __init__(self, f_name):
        self.type = "document"
        self.f_name = {
            f_name.absolute().name
            if isinstance(f_name, Path)
            else Path(str(f_name)).name
        }

    def process_dir(self, dir_path):
        pass


class Metadata:

    def extract_author_information(self, author):
        middle = ""
        for m in author['middle'] if 'middle' in author else "":
            middle = middle + " " + m
        if middle:
            middle = middle + " "
        else:
            middle = " "

        author_name = "<span class=\"author\">" + (
                str(author['last']) + str(author['suffix']) + str(author['first']) + middle).rstrip() + "</span>"

        if author["email"] is not None:
            email = "<span class=\"email\">" + str(author["email"]) if "email" in author else "" + "</span>"
        if author["email"] is None:
            email = ""

        user_info = list()
        if author['affiliation']:
            affiliation = author['affiliation']
            user_info.append(affiliation['laboratory'])
            user_info.append(affiliation['institution'])

            if affiliation['location']:
                location = affiliation['location']
                user_info.append(location['postCode'] if "postCode" in location else "")
                user_info.append(location['settlement'] if "settlement" in location else "")
                user_info.append(location['region'] if "region" in location else "")
                user_info.append(location['country'] if "country" in location else "")
                user_info.append(location['addrLine'] if "addrLine" in location else "")

        while "" in user_info:
            user_info.remove("")

        author_extra_info = "<span class=\"name_info\">" + ", ".join(user_info) + "</span>"

        return author_name + "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;" + author_extra_info + "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;" + email

    def __init__(self, metadata, external_metadata_record):

        self.doi = external_metadata_record['doi']
        self.pmcid = external_metadata_record['pmcid']
        self.pubmed_id = external_metadata_record['pubmed_id']
        self.license = external_metadata_record['license']
        self.publish_time = external_metadata_record['publish_time']
        self.journal = external_metadata_record['journal']
        self.who_covidence_id = external_metadata_record['who_covidence_id']
        self.urls = [x.strip() for x in external_metadata_record['url'].split(';')]
        self.source_x = external_metadata_record['source_x']

        if not external_metadata_record['title']:
            self.title = metadata['title'] if "title" in metadata else ""
        else:
            self.title = external_metadata_record['title']

        if not external_metadata_record['authors']:
            authors = list()
            for author in metadata['authors']:
                authors.append(self.extract_author_information(author))
            self.authors = authors
        else:
            authors = list()
            for author in external_metadata_record['authors'].split(';'):
                authors.append("<span class=\"name\">" + author + "</span><br />")
            self.authors = authors


class RefEntries:
    def __init__(self, ref_entries):
        ref_list = list()
        for ref_entry_key, ref_entry_value in ref_entries.items():
            ref_list.append(
                RefEntry(ref_entry_key, ref_entry_value['type'], ref_entry_value['text'],
                         ref_entry_value['latex'] if "latex" in ref_entry_value else "",
                         ref_entry_value['html'] if "html" in ref_entry_value else ""))
        self.ref = ref_list


class RefEntry:
    def __init__(self, ref_name: str, type: str, text: str, latex, html: str):
        self.ref_name = ref_name
        self.type = type
        self.text = text
        self.latex = latex
        self.html = html


class BibEntry:
    def __init__(self, ref_id, title, authors, year, venue, volume, issn, pages):
        self.ref_id = ref_id
        self.title = title
        self.authors = authors
        self.year = year
        self.venue = venue
        self.volume = volume
        self.issn = issn
        self.pages = pages


class BibEntries:
    def __init__(self, bib_entries):
        l = list()
        for bib_entry in bib_entries:
            ref = bib_entries[bib_entry]

            authors = list()
            for author in ref['authors']:
                middle = ""
                for m in author['middle']:
                    middle = middle + " " + m
                if middle:
                    middle = middle + ""
                else:
                    middle = ""
                authors.append((str(author['last']) + " " + str(author['suffix']) + " " + str(
                    author['first']) + middle.strip()).rstrip())

            authors = ", ".join(authors)
            l.append(
                BibEntry(ref['ref_id'] if 'ref_id' in ref else "", ref['title'], authors, ref['year'], ref['venue'],
                         ref['volume'], ref['issn'],
                         ref['pages']))
        self.bib = l


class Section:
    class Item:
        def __init__(self, section, text):
            self.text = text
            self.section = section

    def __init__(self, body_text):
        body = list()
        if isinstance(body_text, list):
            section = ""
            text = ""
            for item in body_text:
                if section == item['section']:
                    text = text + html.escape(item['text']) + "<br /><br />" if "text" in item else ""
                else:
                    if section != "":
                        body.append(Section.Item(section.strip(), text.strip()))
                        text = ""
                        section = ""
                    section = item['section']
                    text = text + html.escape(item['text']) + "<br /><br />" if "text" in item else ""
            body.append(Section.Item(section.strip(), text.strip()))
        self.body = body


class Issuance(COVIDDocument):
    def __init__(self, f_name, destination, metadata_record):
        filename = re.sub('.xml.json|.json', '', os.path.basename(f_name))
        destination_filename = destination + "/" + filename + ".pdf"
        if path.exists(destination_filename):
            print(f"File already exists: {filename}")
        else:
            print(f"--------------- Creating new PDF File: {filename} --------------- ")
            doc_dict = json_read(f_name, metadata_record)
            pdf_write(doc_dict, destination, filename)
            metadata_write(metadata_record, destination, filename)


def json_read(f_name, external_metadata_record):
    s = set()
    with open(f_name, 'r') as json_file:
        data = json.load(json_file)

        abstact_json = data['abstract'] if "abstract" in data else None
        abstract = extract_abstract(abstact_json, external_metadata_record['abstract'])

        doc_dict = {
            'metadata': Metadata(data['metadata'], external_metadata_record),
            'abstracts': abstract,
            'body_texts': Section(data['body_text']),
            'back_matters': Section(data['back_matter']),
            'bib_entries': BibEntries(data['bib_entries']),
            'ref_entries': RefEntries(data['ref_entries'])
        }
        return doc_dict


def pdf_write(doc_dict, destination, output_filename):
    schema_path = os.path.join(PACKAGE_PATH, 'covid19Template.html')
    test_output_file = destination + "/" + output_filename + ".pdf"

    covid_19_template = Template(filename=schema_path)

    # print(covid_19_template.render(doc_dict=doc_dict))
    try:
        HTML(string=covid_19_template.render(doc_dict=doc_dict)).write_pdf(test_output_file)
    except:
        with open(test_output_file + ".failed", "w+b") as failed_file:
            failed_file.close()
            print("Failed to create file: " + test_output_file)
    # with open(test_output_file, "w+b") as output_file:
    #     pdf = pisa.pisaDocument(covid_19_template.render(doc_dict=doc_dict), output_file)
    #
    #     # pdf.registerFont()
    #     print(pdf.err)


def metadata_write(metadata_record, destination, filename):
    data = {'doc_name': filename, 'doc_title': metadata_record['title'],
            'publication_date': metadata_record['publish_time'], "access_timestamp": "2020-01-01 00:00:00.000000"}
    output_filename = destination + "/" + filename + ".pdf.metadata"

    if bool(data):
        with open(output_filename, "w") as output_file:
            json.dump(data, output_file)


def extract_abstract(json_abstract, ext_md_abstract):
    if ext_md_abstract is None:
        return Section(json_abstract)
    else:
        section = Section("")
        body = list()
        body.append(Section.Item("Abstract", ext_md_abstract + "<br />"))
        section.body = body
        return section


def single_process(data_inputs, metadata):
    (m_file, out_dir) = data_inputs

    m_id = multiprocessing.current_process()
    print(
        "%s - [INFO] - Processing: %s - Filename: %s"
        % (
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f'")[:-4],
            str(m_id),
            Path(m_file).name,
        )
    )
    filename = re.sub('.xml.json|.json', '', os.path.basename(m_file))

    metadata_record = metadata[filename] if filename in metadata else None

    Issuance(m_file, out_dir, metadata_record)
    print(
        "%s - [INFO] - Finished Processing: %s - Filename: %s"
        % (
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f'")[:-4],
            str(m_id),
            Path(m_file).name,
        )
    )


def process_dir(dir_path, ignore_files, out_dir="./", metadata_file="metadata.csv", multiprocess=False):
    metadata = load_metadata(metadata_file)
    print(ignore_files)
    p = Path(dir_path).glob("**/*.json")
    files = [x for x in p if x.is_file()]

    ignore_files_list = list()
    if ignore_files is not None:
        with open(ignore_files) as f:
            ignore_files_list = f.read().splitlines()

    for file_path in files:
        filename = os.path.basename(file_path)
        print(filename)
        if filename in ignore_files_list:
            files.remove(file_path)

    data_inputs = [(m_file, out_dir) for m_file in files]
    print("Parsing Multiple Documents: %i", len(data_inputs))

    if multiprocess != -1:
        if multiprocess == 0:
            pool = multiprocessing.Pool(processes=os.cpu_count(), maxtasksperchild=1)
        else:
            pool = multiprocessing.Pool(processes=int(multiprocess), maxtasksperchild=1)
        print("Processing pool: %s", str(pool))
        pool.map(partial(single_process, metadata=metadata), data_inputs, 5)

    else:
        for item in data_inputs:
            single_process(item, metadata)

    print("Successfully PDF Documents: ", len(data_inputs))


def load_metadata(f_name):
    data = {}
    with open(f_name, 'r') as f_in:
        reader = csv.DictReader(f_in)
        for rows in reader:
            sha_list = []

            if 'sha' in rows.keys():
                sha_list = [x.strip() for x in rows['sha'].split(';')]

            for sha_item in sha_list:
                data[sha_item] = rows

            pmcid = rows['pmcid']
            if pmcid:
                data[pmcid] = rows

        return data
