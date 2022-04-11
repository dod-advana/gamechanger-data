import pandas as pd
import re

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
            ents_dict[name] = name_type
            if aliases != '':
                aliases = [i.strip().lstrip() for i in aliases.split(';')]
            for x in aliases:
                ents_dict[x] = name_type
            if parent != '':
                ents_dict[parent] = 'ORG'
        return ents_dict

    # clean the different entity dataframes
    orgs = clean_df(orgs)
    roles = clean_df(roles)

    # extract out the entities as a dictionary
    ents_dict = collect_ents(ents_dict={}, df=orgs, name_type='ORG')
    ents_dict = collect_ents(ents_dict=ents_dict, df=roles, name_type='PERSON')

    for x in must_include.keys():
        if x not in ents_dict.keys():
            ents_dict[x] = must_include[x]
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

def get_entities_from_text(text, entities):
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
        ents = remove_overlapping_entities(ents) # remove overlapping spans
    ents.sort(key=lambda x: x[0], reverse=False)
    # transform tuple into dictionary representation for downstream
    ents_list = [{"span_start":ent[0],
                  "span_end": ent[1],
                  "entity_type":ent[2],
                  "entity_text":ent[3]}
                  for ent in ents]
    return ents_list