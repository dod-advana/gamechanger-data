from gamechangerml.src.search.ranking.features import get_txt_length


def add_txt_length(doc_dict):
    doc_dict["txt_length"] = get_txt_length(doc_dict["id"])
    return doc_dict


def add_word_count(doc_dict):
    doc_dict["word_count"] = len(doc_dict["text"].split(" "))
    return doc_dict
