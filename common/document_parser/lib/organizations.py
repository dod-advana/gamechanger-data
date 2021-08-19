from gamechangerml.src.search.ranking.features import get_orgs


def add_orgs_rs(doc_dict):
    doc_dict["orgs_rs"] = get_orgs(doc_dict["id"])
    return doc_dict
