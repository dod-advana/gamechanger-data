import re
from typing import Iterable, List

import syntok.segmenter as segmenter
import syntok.tokenizer as tokenizer
from gamechangerml.src.utilities.text_utils import utf8_pass


def get_paragraph_text(segmented: Iterable[List[tokenizer.Token]]) -> str:
    sentences = []
    for sentence in segmented:
        sentence_text = ''.join(
            [token.spacing + token.value for token in sentence]
        )
        # substitute newlines that do not have whitespace before or after with a space
        sentence_text = re.sub(r'(?<=\S)\n(?=\S)', ' ', sentence_text)
        # strip any remaining newlines
        sentence_text = sentence_text.replace('\n', '')
        # clean any extra whitespace at the beginning or end
        sentence_text = sentence_text.strip()
        sentences.append(sentence_text)
    par_text = ' '.join(sentences)
    return par_text


def create_paragraph_dict(page_num, paragraph_num, paragraph_text, doc_dict):
    par = {}
    par["type"] = "paragraph"
    par["filename"] = doc_dict["filename"]
    par["par_inc_count"] = doc_dict["par_count_i"]
    par["id"] = doc_dict["filename"] + "_" + str(doc_dict["par_count_i"])
    doc_dict["par_count_i"] += 1
    par["par_count_i"] = paragraph_num
    par["page_num_i"] = page_num
    
    paragraph_text = handle_DoD_text(paragraph_text)
    
    par["par_raw_text_t"] = utf8_pass(paragraph_text).replace('  ',' ')

    par["entities"] = []

    return par

def handle_DoD_text(text):
    text = text.replace('Do D', 'DoD ') #splitting up things like 'Do Dapproved'
    
    text = text.replace('DoD M', 'DoDM') #recombining DoD doc types
    text = text.replace('DoD I', 'DoDI')
    text = text.replace('DoD D', 'DoDD')
    
    text = text.replace('DoD epth', 'Do Depth') #Catching remaining edge-cases that were found
    text = text.replace('DoD uring', 'Do During') #there might be more that were not seen in testing
    
    return text
    
    
def handle_page_paragraphs(page_num, page_text, doc_dict):
    for paragraph_num, paragraph in enumerate(segmenter.process(page_text)):
        paragraph_text = get_paragraph_text(paragraph)
        paragraph_dict = create_paragraph_dict(
            page_num, paragraph_num, paragraph_text, doc_dict)
        doc_dict["paragraphs"].append(paragraph_dict)


def handle_paragraphs(doc_dict):
    doc_dict["paragraphs"] = []
    for page_num, page in enumerate(doc_dict["pages"]):
        page_text = page["p_raw_text"]
        handle_page_paragraphs(page_num, page_text, doc_dict)
