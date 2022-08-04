import re

from gamechangerml.src.utilities.text_utils import simple_clean


def extract_entities(
    document,
    spacy_model,
    entity_types=("ORG", "GPE", "NORP", "LAW", "LOC", "PERSON"),
):
    """
    Creates a dictionary of entities in a given document using the provided NER model.

    Args:
        document (str): Input string
        spacy_model (Spacy model): pre-built spacy model from GC utilities
        entity_types (list): Default list of entity types to keep

    Returns:
        dict
    """
    cleaned_text = simple_clean(document)
    doc = spacy_model(cleaned_text)
    entities = {}

    for i in entity_types:
        entities[i] = []

    for entity in doc.ents:
        if entity.label_ in entities.keys():
            entities[entity.label_].append(entity.text)

    for i in entities.keys():
        entities[i] = list(set(entities[i]))

    return entities


def create_list_from_dict(mydict):
    """
    Converts entities dictionary to flat list.

    Args:
        mydict (dict): Input entities dictionary

    Returns:
        list
    """
    outputs = []
    for k, v in mydict.items():
        if len(v) > 0:
            for i in v:
                outputs.append(i)

    return outputs


def remove_articles(entities_list):
    """
    Removes articles from entity names.

    Args:
        entities_list (list): List of input strings

    Returns:
        list
    """
    text_list = entities_list
    for i, v in enumerate(text_list):
        if v[0:4] == "the ":
            text_list[i] = v.replace("the ", "")
        elif v[0:4] == "The ":
            text_list[i] = v.replace("The ", "")

    return text_list


def remove_hanging_parenthesis(sample_string):
    """
    Removes parenthesis at the end of strings.

    Args:
        sample_string (str): Input string

    Returns:
        str
    """
    return re.sub(r"[^.*]\($", "", sample_string).strip()


def match_parenthesis(entities_list):
    """
    Fixes issues with mismatched parenthesis in a string.

    Args:
        entities_list (list): List of input strings

    Returns:
        list
    """
    text_list = entities_list

    for i, v in enumerate(text_list):
        clean_text = remove_hanging_parenthesis(v)
        if "(" in clean_text:
            if ")" not in clean_text:
                paren_split = clean_text.split("(")
                paren_add = paren_split[1].split(" ", 1)
                if len(paren_add) > 1:
                    clean_text = (
                        paren_split[0]
                        + "("
                        + paren_add[0]
                        + ") "
                        + paren_add[1]
                    )
                else:
                    clean_text = paren_split[0] + "(" + paren_add[0] + ") "
        text_list[i] = clean_text

    text_list = [i for i in text_list if i]

    return text_list
