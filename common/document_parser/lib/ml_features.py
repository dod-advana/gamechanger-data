from gamechangerml.src.search.ranking import features as ft


def add_pagerank_r(doc_dict):
    doc_dict["pagerank_r"] = ft.get_pr(doc_dict["id"])
    return doc_dict


def add_popscore_r(doc_dict):
    doc_dict["pop_score"] = ft.get_pop_score(doc_dict["filename"])
    return doc_dict


def add_orgs_rs(doc_dict):
    doc_dict["orgs_rs"] = ft.get_orgs(doc_dict["id"])
    return doc_dict


def add_kw_doc_score_r(doc_dict):
    doc_dict["kw_doc_score_r"] = ft.get_kw_score(doc_dict["id"])
    return doc_dict


def add_txt_length(doc_dict):
    doc_dict["txt_length"] = ft.get_txt_length(doc_dict["id"])
    return doc_dict
