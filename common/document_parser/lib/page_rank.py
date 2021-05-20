from gamechangerml.src.search.ranking.features import get_pr


def add_pagerank_r(doc_dict):
    doc_dict["pagerank_r"] = get_pr(doc_dict["id"])
    return doc_dict
