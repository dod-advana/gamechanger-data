def add_word_count(doc_dict):
    doc_dict["word_count"] = len(doc_dict["text"].split(" "))
    return doc_dict
