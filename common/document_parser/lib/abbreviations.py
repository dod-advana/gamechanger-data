from gamechangerml.src.featurization.abbreviation import expand_abbreviations


def add_abbreviations_n(doc_dict):
    _, abbreviations = expand_abbreviations(doc_dict["text"])
    doc_dict["abbreviations_n"] = abbreviations
    return doc_dict
