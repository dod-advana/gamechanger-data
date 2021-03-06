from gamechangerml.src.utilities.text_utils import simple_clean, utf8_pass
import gamechangerml.src.utilities.spacy_model as spacy_
from common.document_parser.lib.entities_utils import *
import collections
import os
from gamechangerml import DATA_PATH

spacy_model = spacy_.get_lg_nlp()
entities_dict = make_entities_dict(os.path.join(DATA_PATH,"features/GraphRelations.xls"))

def extract_entities(doc_dict):
    # Utilizes GraphRelations.xlsx in gamechangerml to find gold standard entities within each page's text. Then, check
    # if the entities are mentioned in the paragraphs and append to paragraph  metadata.
    all_ents = []
    for par in doc_dict["paragraphs"]:
        par_entities_dict = {
            "ORG": [],
            "GPE": [],
            "NORP": [],
            "LAW": [],
            "LOC": [],
            "PERSON": [],
        }
        # clean and get entities from paragraph
        par_text = par["par_raw_text_t"]
        par_text = simple_clean(par_text)
        par_entities = get_entities_from_text(par_text, entities_dict)

        ## extract out non-duplicative entities
        for entity in par_entities:
            par_entities_dict[entity['entity_type']].append(entity["entity_text"])

        entity_json = {
            "ORG_s": list(set(par_entities_dict["ORG"])),
            "GPE_s": list(set(par_entities_dict["GPE"])),
            "NORP_s": list(set(par_entities_dict["NORP"])),
            "LAW_s": list(set(par_entities_dict["LAW"])),
            "LOC_s": list(set(par_entities_dict["LOC"])),
            "PERSON_s": list(set(par_entities_dict["PERSON"])),
        }
        par["entities"] = entity_json
        all_ents = all_ents + sum(entity_json.values(), [])

    counts = collections.Counter(all_ents)

    doc_dict['entities'] = list(set(all_ents))
    doc_dict["top_entities_t"] = [x[0] for x in counts.most_common(5)]
    return doc_dict

def extract_entities_spacy(doc_dict):
    # OLD Function utilizing Spacy to extract out entities. Get entities in each page then check if the entities are mentioned in the paragraphs and append
    # to paragraph  metadata.
    page_dict = {}
    for page in doc_dict["pages"]:
        page_text = utf8_pass(page["p_raw_text"])
        page_text = simple_clean(page_text)
        doc = spacy_model(page_text)
        page_dict[page["p_page"]] = doc
    all_ents = []
    for par in doc_dict["paragraphs"]:
        par_entities_dict = {
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
                par_entities_dict[entity.label_].append(entity.text)

        entity_json = {
            "ORG_s": list(set(par_entities_dict["ORG"])),
            "GPE_s": list(set(par_entities_dict["GPE"])),
            "NORP_s": list(set(par_entities_dict["NORP"])),
            "LAW_s": list(set(par_entities_dict["LAW"])),
            "LOC_s": list(set(par_entities_dict["LOC"])),
            "PERSON_s": list(set(par_entities_dict["PERSON"])),
        }

        par["entities"] = entity_json
        all_ents = all_ents + sum(entity_json.values(), [])
    counts = collections.Counter(all_ents)
    doc_dict["top_entities_t"] = [x[0] for x in counts.most_common(5)]
    return doc_dict
