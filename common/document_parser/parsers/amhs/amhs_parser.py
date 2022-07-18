import fitz
import json


def substring_after(s: str, delim: str):
    return s.partition(delim)[2]


def get_pages(s: str):
    substr = substring_after(s, "PAGE").split("\n")[0].strip()
    first_pg = int(substr[0])
    last_pg = int(substr[-1])

    return first_pg, last_pg


def extract_sections(doc: fitz.Document, txt: str, offset: int = 0):
    """extract_sections - parses sections from a PDF document
    txt : Document - opened PDF document
    offset : int - the offset of pages
    """
    first_pg, last_pg = get_pages(txt)
    broken_txt = txt.partition("UNCLASSIFIED//")
    header_sections = broken_txt[0].split(": ")
    body = broken_txt[-1]
    values = []
    names = ["title"]
    for i in header_sections:
        field = i.split("\n")[-1]
        names.append(field)

    for i in range(0, len(header_sections)):
        if i != 0:
            field = "".join(header_sections[i].split("\n")[:-1])
            values.append(field)
        elif i == 0:
            values.append("".join(header_sections[i].split("\n")[:-1]))
    txt_dict = dict(zip(names, values))

    for i in range(1 + offset, offset + last_pg):
        txt = doc.get_page_text(i)
        body += txt
    txt_dict["Body"] = body
    txt_dict["pages"] = last_pg
    txt_dict["classification"] = broken_txt[1]
    return txt_dict


def write_json(filename, obj):
    with open(filename + ".json", "w") as fp:
        json.dump(obj, fp)


def extract_document(filename: str):
    txt_orders = []
    doc = fitz.open(filename)
    offset = 0
    while offset < doc.pageCount:
        curr_order = doc.getPageText(offset)
        txt_dict = extract_sections(doc, curr_order, offset=offset)
        txt_orders.append(txt_dict)
        offset += txt_dict["pages"]
    return txt_orders
