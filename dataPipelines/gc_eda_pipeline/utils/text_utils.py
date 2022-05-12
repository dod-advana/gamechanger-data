import re
from string import punctuation

punct = set(punctuation)

def utf8_pass(text):
    return text.encode("utf-8", "ignore").decode("utf-8")


def clean_text(doc_text: str) -> str:
    """
    The text is cleaned from special characters and extra spaces
    Args:
        doc_text: input text to be cleaned

    Returns:

    """

    text = doc_text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    remove = punctuation + "”“"
    remove = remove.replace(".", "")

    text = text.translate({ord(i): None for i in remove})

    return text

def extract_sow_pws(text):
    """
    Extracts out the SOW/PWS for EDA contracts
    Args:
        text: Raw text of the EDA contract

    Returns:SOW/PWS text for the contract if found, if not found, returns None

    """
    sow_regex_list = ['Section C.*-',"'SECTION C.*-'",'PERFORMANCE WORK STATEMENT','STATEMENT OF WORK']
    for sow_regex in sow_regex_list:
        sow_exist = re.search(sow_regex, text)
        if sow_exist:
            sow_pws_start = sow_exist.span()[0]
        else:
            continue
        sow_pws_end = re.search('Section [D-Z].*-', text[sow_pws_start:])
        if sow_pws_end is None:
            sow_pws_end = len(text)
        else:
            sow_pws_end = sow_pws_start + sow_pws_end.span()[0]
        sow_pws_text = text[sow_pws_start:sow_pws_end]
        return sow_pws_text
    return ""