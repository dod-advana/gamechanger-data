from gamechangerml.src.featurization.rank_features import features as ft

def add_pagerank_r(doc_dict):
    doc_dict["pagerank_r"] = ft.get_pr(doc_dict["id"])
    return doc_dict

def add_popscore_r(doc_dict):
    doc_dict["pop_score"] = ft.get_pop_score(doc_dict["filename"])
    return doc_dict