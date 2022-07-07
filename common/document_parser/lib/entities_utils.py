from pandas import read_excel
from re import sub
from collections import Counter
from operator import itemgetter


def make_entities_lookup_dict(
    entities_path,
    must_include={"DoD": "ORG", "DOD": "ORG", "Department of Defense": "ORG"},
):
    """Load the Graph Relations (.xls) file from gamechangerml and create the 
    entity lookup dictionary.

    Args:
        entities_path (str): Path to the Graph Relations (.xls) file in 
            gamechangerml that contains the entities to look for in documents.
        must_include (dict, optional): Dictionary such that keys are (str) 
            entities and values are (str) entity types. These will be added to 
            the entities lookup dictionary, even if they are not present in the 
            file at entities_path. Defaults to 
            {"DoD": "ORG", "DOD": "ORG", "Department of Defense": "ORG"}.
            
    Returns:
        dict: Dictionary such that: 
            - keys (str) are the entities as they should be searched for in the 
                text, containing only alphanumeric characters.
            - values (dict) contains:
                - key "raw_ent" with corresponding values (str) that are the 
                    entities in the form that they should be added to a 
                    document's metadata.
                - key "ent_type" with corresponding values (str) that are the 
                    type of entity (GPE, LOC, etc.)

            Example: { "USC Title 10A": {"raw_ent": "U.S.C. Title 10-A", "ent_type": "LAW"}}

    """
    dfs = [
        (read_excel(io=entities_path, sheet_name="Orgs"), "ORG"),
        (read_excel(io=entities_path, sheet_name="Roles"), "PERSON"),
    ]
    ents_dict = {}

    for df, ent_type in dfs:
        df.dropna(subset=["Name"], inplace=True)
        cols = [
            col
            for col in df.columns
            if col in ["Name", "Parent", "OrgParent", "Aliases"]
        ]

        for col in cols:
            df[col].fillna("", inplace=True)
            df[col] = df[col].apply(lambda x: x.strip())
            for ent in df[col]:
                if col == "Aliases":
                    for alias in ent.split(";"):
                        if ent != "":
                            ents_dict[replace_nonalpha_chars(ent, "")] = {
                                "raw_ent": alias,
                                "ent_type": ent_type,
                            }
                else:
                    if ent != "":
                        ents_dict[replace_nonalpha_chars(ent, "")] = {
                            "raw_ent": ent,
                            "ent_type": ent_type,
                        }

        for ent, ent_type in must_include.items():
            if ent != "" and ent not in ents_dict.keys():
                ents_dict[replace_nonalpha_chars(ent, "")] = {
                    "raw_ent": ent,
                    "ent_type": ent_type,
                }

    return ents_dict


def remove_overlapping_ents(ents):
    """Remove overlapping entities. 

    Entities are considered overlapping if they share the same start or end 
    index. If entities overlap, only keep the longest one.

    Args:
        ents (list of tuple): List of tuples. Each tuple represents an entity 
        and should have the following values at index 0 and index 1:
                int: start index of the entity
                int: end index of the entity
    Returns:
        list of tuple: Non-overlapping entities
    """
    repeated_starts = [
        x for x, y in Counter(ent[0] for ent in ents).most_common() if y > 1
    ]
    # For entities that share a start index, only keep the one with the
    # largest end index.
    largest_of_repeats = [
        max([ent for ent in ents if ent[0] == start], key=itemgetter(1))
        for start in repeated_starts
    ]
    # Remove all entities that have a shared start index. Then, add back the
    # largest of those overlapping entities.
    ents = [
        ent for ent in ents if ent[0] not in repeated_starts
    ] + largest_of_repeats

    repeated_ends = [
        x for x, y in Counter(ent[1] for ent in ents).most_common() if y > 1
    ]
    # For entities that share an end index, only keep the one with the
    # smallest start index.
    largest_of_repeats = [
        min([ent for ent in ents if ent[1] == end], key=itemgetter(0))
        for end in repeated_ends
    ]
    # Remove all entities that have a shared end index. Then, add back the
    # largest of those overlapping entities.
    ents = [
        ent for ent in ents if ent[1] not in repeated_ends
    ] + largest_of_repeats

    return ents


def replace_nonalpha_chars(text, replace_char=""):
    """Replace non-alphanumeric characters in the text.

    Args:
        text (str)
        replace_char (str, optional): The character(s) to replace 
            non-alphanumeric characters with. Defaults to "".

    Returns:
        str: The text with non-alphanumeric characters replaced.
    """
    return sub("[^a-zA-Z0-9\s]+", replace_char, text)

