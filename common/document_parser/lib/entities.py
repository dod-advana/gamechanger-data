from os.path import join
from collections import Counter
from itertools import chain
from flashtext import KeywordProcessor

from gamechangerml import DATA_PATH
from gamechangerml.src.utilities.text_utils import simple_clean

from common.document_parser.lib.document import Document, FieldNames
from common.document_parser.lib.entities_utils import (
    remove_overlapping_ents,
    replace_nonalpha_chars,
    make_entities_lookup_dict,
)


# The graph relations file from gamechangerml is used as gold standard entities.
ENTITIES_LOOKUP_DICT = make_entities_lookup_dict(
    join(DATA_PATH, "features/GraphRelations.xls")
)

# Used to find entities in text.
PROCESSOR = KeywordProcessor(case_sensitive=True)
for ent in ENTITIES_LOOKUP_DICT.keys():
    PROCESSOR.add_keyword(ent)

# Used to rename entity types from how they exist in the graph relations file
# to how they will exist in document dictionaries.
ENTITY_RENAME_DICT = {
    "ORG": "ORG_s",
    "GPE": "GPE_s",
    "NORP": "NORP_s",
    "LAW": "LAW_s",
    "LOC": "LOC_s",
    "PERSON": "PERSON_s",
}


def extract_entities(doc_dict):
    """Extract entities from a document's text.

    Utilizes GraphRelations.xls from gamechangerml as gold standard entities.


    Adds the following new keys/ values to doc_dict:
        "entities" (list of str): Entities extracted from the document.
        "top_entities_t" (list of str): Most common entities in the document

    Also adds the following to each item of doc_dict["paragraphs"]:
        "entities" (dict): Keys (str) are entity types and values (list of str)
            are the entities extracted from the paragraph.
    Args:
        doc_dict (dict): Dictionary representation of a document. Must have
            the following keys/ values:
                "paragraphs" (list of dict): Dictionary representations of the
                    document's paragraphs. Each dict must have the key
                    "par_raw_text_t" with the corresponding value (str) being
                    the paragraph's text.
            Example:
            {
                "paragraphs": [
                    {
                        "par_raw_text_t": "hello"
                    }
                ]
            }

    Returns:
        dict: The updated document dictionary
    """
    doc = Document(doc_dict)
    paragraphs = doc.get_field(FieldNames.PARAGRAPHS)
    all_ents = []

    for par in paragraphs:
        ents_by_type = dict(
            zip(
                list(ENTITY_RENAME_DICT.values()),
                [set() for _ in range(len(ENTITY_RENAME_DICT))],
            )
        )

        text = par.get(FieldNames.PAR_RAW_TEXT)
        if text is None:
            par[FieldNames.ENTITIES] = ents_by_type
            continue
        text = simple_clean(text)
        # Remove non-alphanumeric characters in the paragraph's text since we
        # search for entities using the keys of ENTITIES_LOOKUP_DICT which also
        # have non-alphanumeric characters removed.
        text = replace_nonalpha_chars(text, "")

        # The flashtext KeywordProcessor (inspired by the Aho-Corasick
        # algorithm and Trie data structure) is MUCH faster than re.finditer()
        # in this case.
        ents = [
            (
                e[1],
                e[2],
                ENTITIES_LOOKUP_DICT[e[0]]["raw_ent"],
                ENTITIES_LOOKUP_DICT[e[0]]["ent_type"],
            )
            for e in PROCESSOR.extract_keywords(text, span_info=True)
        ]
        ents = remove_overlapping_ents(ents)
        for ent in ents:
            ents_by_type[ENTITY_RENAME_DICT[ent[3]]].add(ent[2])
        ents_by_type = {k: list(v) for k, v in ents_by_type.items()}

        doc.set_paragraph_entities(par, ents_by_type)
        all_ents += list(chain.from_iterable(ents_by_type.values()))

    doc.set_field(FieldNames.ENTITIES, (list(set(all_ents))))
    doc.set_field(
        FieldNames.TOP_ENTITIES,
        ([ent[0] for ent in Counter(all_ents).most_common(5)]),
    )

    return doc.doc_dict
