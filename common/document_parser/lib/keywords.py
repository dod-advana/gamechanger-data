from collections import defaultdict
from gamechangerml.src.featurization.rank_features.features import get_kw_score


def add_keyw_5(doc_dict):
    keyword_counts = defaultdict(int)
    for l in doc_dict["keyw_5"]:
        for kw in l:
            keyword_counts[kw] += 1
    kw_list = list(zip(keyword_counts.values(), keyword_counts.keys()))
    kw_list.sort(reverse=True)
    doc_dict["keyw_5"] = [x[1] for x in kw_list[:10]]
    return doc_dict