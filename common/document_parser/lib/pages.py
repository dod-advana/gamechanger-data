from dataScience.src.utilities.text_utils import utf8_pass, clean_text
from dataScience.src.featurization.keywords.extract_keywords import get_keywords


def create_page_dict(page_num, page_text, doc_dict):
    cleaned_text = clean_text(page_text)
    utf8_ptext = utf8_pass(cleaned_text)
    page_dict = {}
    page_dict["type"] = "page"
    page_dict["p_text"] = utf8_ptext
    doc_dict["keyw_5"].append(get_keywords(page_text))
    page_dict["p_raw_text"] = page_text
    page_dict["p_page"] = page_num
    page_dict["filename"] = doc_dict["filename"]
    page_dict["id"] = str(doc_dict["filename"]) + "_" + str(page_num)
    doc_dict["page_count"] += 1
    return page_dict


def handle_page(page_num, page_text, doc_dict):
    page_dict = create_page_dict(page_num, page_text, doc_dict)
    doc_dict["pages"].append(page_dict)


def handle_pages(doc_obj, doc_dict):
    doc_dict["text"] = ""
    doc_dict["page_count"] = 0
    doc_dict["pages"] = []
    doc_dict["keyw_5"] = []
    for page_num, page in enumerate(doc_obj.pages()):
        page_text = page.getText()
        doc_dict["text"] = doc_dict["text"] + page_text
        handle_page(page_num, page_text, doc_dict)
