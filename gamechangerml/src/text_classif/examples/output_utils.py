import numpy as np

from gamechangerml.src.featurization.extract_improvement.extract_utils import (
    extract_entities,
    create_list_from_dict,
    remove_articles,
    match_parenthesis,
)


def get_agency(df, spacy_model):
    """
    Extract potential agencies from responsibilities text and cleans output.

    Args:
    df: Input responsibilities dataframe
    spacy_model: Spacy langauge model (typically 'en_core_web_lg')

    Returns:
    [List]
    """
    clean_df = df["agencies"].replace(np.nan, "", regex=True)
    all_docs = []

    for i in range(df.shape[0]):
        sentence = df["sentence"][i]
        entities = extract_entities(sentence, spacy_model)

        prev_agencies = [x.strip() for x in df["agencies"][i].split(",")]
        prev_agencies = [i for i in prev_agencies if i]

        flat_entities = create_list_from_dict(entities)
        for j in prev_agencies:
            flat_entities.append(j)

        flat_entities = remove_articles(flat_entities)
        flat_entities = match_parenthesis(flat_entities)
        flat_entities = "|".join(i for i in set(flat_entities))
        all_docs.append(flat_entities)

    df["agencies"] = all_docs
    return df
