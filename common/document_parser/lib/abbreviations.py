from gamechangerml.src.featurization.abbreviation import expand_abbreviations


def add_abbreviations_n(doc_dict):
    # TODO: (09/09/2021) Improve abbreviation processing time.
    # TODO: (09/09/2021) Process abbreviations separate from parsing.
    _, abbreviations = ("", []) # expand_abbreviations(doc_dict["text"])
    doc_dict["abbreviations_n"] = abbreviations
    return doc_dict
