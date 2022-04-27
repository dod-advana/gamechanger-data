import pandas as pd
import re

def replace_nonalpha_chars(text, replace_char=""):
    return re.sub("[^a-zA-Z\s]+", replace_char, text)

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

    def collect_ents(ents_dict, df, name_type):
        '''Update a dictionary with names, aliases, parents and types from a df'''
        for i in df.index:
            name = df.loc[i, 'Name'].strip().lstrip()
            aliases = df.loc[i, 'Aliases']
            parent = df.loc[i, 'Parent'].strip().lstrip()
            ents_dict[replace_nonalpha_chars(name)] = {"ent_type":name_type,"raw_ent":name}
            if "OrgParent" in df.columns:
                org_parent = df.loc[i, 'Parent'].strip().lstrip()
                if org_parent!="":
                    ents_dict[replace_nonalpha_chars(org_parent)] = {"ent_type": "ORG", "raw_ent": org_parent}

            if aliases != '':
                aliases = [i.strip().lstrip() for i in aliases.split(';')]
                for alias in aliases:
                    ents_dict[replace_nonalpha_chars(alias)] = {"ent_type":name_type,"raw_ent":alias}
            if parent != '':
                ents_dict[replace_nonalpha_chars(parent)] = {"ent_type":name_type,"raw_ent":parent}
        return ents_dict

    # clean the different entity dataframes
    orgs = clean_df(orgs)
    roles = clean_df(roles)

    # extract out the entities as a dictionary
    ents_dict = collect_ents(ents_dict={}, df=orgs, name_type='ORG')
    ents_dict = collect_ents(ents_dict=ents_dict, df=roles, name_type='PERSON')

    for x in must_include.keys():
        if x not in ents_dict.keys():
            ents_dict[replace_nonalpha_chars(x)] = {"ent_type":must_include[x],"raw_ent":x}
    if "" in ents_dict:
        ents_dict.pop("")
    return ents_dict

def remove_overlapping_entities(ents):
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

def sort_list_by_str_length(l):
    l.sort(key=lambda s: len(s),reverse=True)
    return l

def get_entities_from_text(text, entities_dict):
    '''Lookup entities in single page of text, remove overlapping (shorter) spans'''
    ents = []
    text = replace_nonalpha_chars(text)
    sorted_ent_keys = sort_list_by_str_length(list(entities_dict.keys()))
    # combine all search terms into single regex (using word bounds around each word for to ensure aliases are not part
    # of a larger word)
    for match in re.finditer(r"(?=(\b" + r'\b|\b'.join(sorted_ent_keys) + r"\b))", text):
        tup = (match.regs[1][0], match.regs[1][1], entities_dict[match[1]]["ent_type"], entities_dict[match[1]]["raw_ent"])
        ents.append(tup)
    if ents != []:
        ents = remove_overlapping_entities(ents) # remove overlapping spans
    ents.sort(key=lambda x: x[0], reverse=False)
    # transform tuple into dictionary representation for downstream
    ents_list = [{"span_start":ent[0],
                  "span_end": ent[1],
                  "entity_type":ent[2],
                  "entity_text":ent[3]}
                  for ent in ents]
    return ents_list