from gamechangerml.src.utilities.text_utils import simple_clean, utf8_pass
import gamechangerml.src.utilities.spacy_model as spacy_
import collections

spacy_model = spacy_.get_lg_nlp()


def extract_entities(doc_dict):
    # get entities in each page. then, check if the entities are mentioned in the paragraphs and append
    # to paragraph  metadata.
    page_dict = {}
    for page in doc_dict["pages"]:
        page_text = utf8_pass(page["p_raw_text"])
        page_text = simple_clean(page_text)
        doc = spacy_model(page_text)
        page_dict[page["p_page"]] = doc
    all_ents = []
    for par in doc_dict["paragraphs"]:
        entities = {
            "ORG": [],
            "GPE": [],
            "NORP": [],
            "LAW": [],
            "LOC": [],
            "PERSON": [],
        }
        par_text = par["par_raw_text_t"]
        par_text = simple_clean(par_text)
        doc = page_dict[par["page_num_i"]]

        # doc is spacy obj
        for entity in doc.ents:
            if (
                entity.label_ in ["ORG", "GPE", "LOC", "NORP", "LAW", "PERSON"]
                and entity.text in par_text
            ):
                entities[entity.label_].append(entity.text)

        entity_json = {
            "ORG_s": list(set(entities["ORG"])),
            "GPE_s": list(set(entities["GPE"])),
            "NORP_s": list(set(entities["NORP"])),
            "LAW_s": list(set(entities["LAW"])),
            "LOC_s": list(set(entities["LOC"])),
            "PERSON_s": list(set(entities["PERSON"])),
        }

        par["entities"] = entity_json
        all_ents = all_ents + sum(entity_json.values(), [])
    counts = collections.Counter(all_ents)
    doc_dict["top_entities_t"] = [x[0] for x in counts.most_common(5)]
    return doc_dict
