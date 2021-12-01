from gamechangerml.src.featurization.rank_features.features import get_txt_length

def add_word_count(doc_dict):
    doc_dict["word_count"] = len(doc_dict["text"].split(" "))
    return doc_dict
