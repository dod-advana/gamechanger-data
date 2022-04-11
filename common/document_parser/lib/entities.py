from gamechangerml.src.utilities.text_utils import simple_clean, utf8_pass
import gamechangerml.src.utilities.spacy_model as spacy_
import collections
import pandas as pd
import re
import os
from gamechangerml import DATA_PATH

spacy_model = spacy_.get_lg_nlp()

def make_entities_dict(
        entities_path,
        must_include={'DoD': 'ORG', 'Department of Defense': 'ORG', 'DOD': 'ORG'}
):
    '''Makes dictionary of org/roles/aiases/parents and their types'''

    orgs = pd.read_excel(io=entities_path, sheet_name='Orgs')
    roles = pd.read_excel(io=entities_path, sheet_name='Roles')

    def clean_df(df):
        '''Clean the df before getting entities'''
        df.dropna(subset=["Name"], inplace=True)
        df['Parent'].fillna('', inplace=True)
        df['Aliases'].fillna('', inplace=True)
        return df

    orgs = clean_df(orgs)
    roles = clean_df(roles)

    def collect_ents(ents_dict, df, name_type):
        '''Update a dictionary with names, aliases, parents and types from a df'''
        for i in df.index:
            name = df.loc[i, 'Name'].strip().lstrip()
            aliases = df.loc[i, 'Aliases']
            parent = df.loc[i, 'Parent'].strip().lstrip()
            ents_dict[name] = name_type
            if aliases != '':
                aliases = [i.strip().lstrip() for i in aliases.split(';')]
            for x in aliases:
                ents_dict[x] = name_type
            if parent != '':
                ents_dict[parent] = 'ORG'
        return ents_dict

    ents_dict = collect_ents(ents_dict={}, df=orgs, name_type='ORG')
    ents_dict = collect_ents(ents_dict=ents_dict, df=roles, name_type='PERSON')

    for x in must_include.keys():
        if x not in ents_dict.keys():
            print(f"Adding {x}")
            ents_dict[x] = must_include[x]
    if "" in ents_dict:
        ents_dict.pop("")
    return ents_dict

def get_longest(ents):
    '''Get the longest entity spans in text (remove shortest overlapping)'''

    ents.sort(key=lambda x: x[0], reverse=True)  # sort by last (start of span)
    remove = []
    full_range = len(ents) - 1
    for i in range(full_range):  # for each entity, compare against remaining entities
        remainder = range(full_range - i)
        n = i + 1
        for x in remainder:
            if ents[i][0] < ents[n][1]:
                if len(ents[i][3].split()) > len(ents[n][3].split()):  # remove the shortest
                    remove.append(n)
                else:
                    remove.append(i)
            n += 1

    remove = list(set(remove))
    remove.sort()
    for x in remove[::-1]:
        try:
            ents.remove(ents[x])
        except:
            pass
    return ents

def get_ents(text, entities):
    '''Lookup entities in single page of text, remove overlapping (shorter) spans'''
    ents = []
    for x in entities.keys():
        try:
            pattern = r"\b{}\b".format(x)
            for match in re.finditer(pattern, text):
                tup = (match.start(), match.end(), entities[x], text[match.start():match.end()])
                ents.append(tup)
        except Exception as e:
            print(e)
    if ents != []:
        ents = get_longest(ents) # remove overlapping spans
    ents.sort(key=lambda x: x[0], reverse=False)
    ents_list = [{"span_start":ent[0],
                  "span_end": ent[1],
                  "entity_type":ent[2],
                  "entity_text":ent[3]}
                  for ent in ents]
    return ents_list

doc_dict = {"pages":[{"p_raw_text": "United States of America has a capital of Washington, DC and the head person is President Joe Biden, United States of America, the President of the United States","p_page":0}],
            "paragraphs": [{"par_raw_text_t":"United States of America has a capital of Washington, DC and the head person is President Joe Biden, United States of America, the President of the United States","page_num_i":0}]}

def extract_entities(doc_dict):
    # get entities in each page. then, check if the entities are mentioned in the paragraphs and append
    # to paragraph  metadata.

    entities_dict = make_entities_dict(os.path.join(DATA_PATH,"features/GraphRelations.xls"))
    page_dict = {}
    for page in doc_dict["pages"]:
        page_text = utf8_pass(page["p_raw_text"])
        page_text = simple_clean(page_text)
        page_entities = get_ents(page_text,entities_dict)
        page_dict[page["p_page"]] = page_entities
    all_ents = []
    for par in doc_dict["paragraphs"]:
        entities = {
            "ORG": [],
            "GPE": [],
            "NORP": [],
            "LAW": [],
            "LOC": [],
            "PERSON": []
        }
        par_text = par["par_raw_text_t"]
        par_text = simple_clean(par_text)
        page_entities = page_dict[par["page_num_i"]]

        # doc is spacy obj
        for entity in page_entities:
            if (
                    entity['entity_type'] in ["ORG", "GPE", "LOC", "NORP", "LAW", "PERSON"]
                    and entity["entity_text"] in par_text
            ):
                entities[entity['entity_type']].append(entity["entity_text"])

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


def extract_entities_spacy(doc_dict):
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
