import logging
from transformers import pipeline
from gamechangerml.src.utilities.text_generators import gen_json, child_doc_gen
from gamechangerml.src.utilities.text_utils import simple_clean
import os
import glob
from transformers import AutoTokenizer, AutoModelForTokenClassification
import torch

# TODO: format output
# TODO: add timing to get time of running HF vs spacy
# TODO: write tests to see how good both NERs are


def load_text(corpus_dir):
    if not os.path.isdir(corpus_dir):
        raise FileNotFoundError(
            "directory not found; got {}".format(corpus_dir)
        )
    return ner_dir(corpus_dir)


# TODO: update
def ner_dir(corpus_dir):
    doc_gen = gen_json(corpus_dir)
    for text, f_name in child_doc_gen(doc_gen):
        text = simple_clean(text)
        yield text


if __name__ == "__main__":
    from collections import defaultdict

    model = AutoModelForTokenClassification.from_pretrained(
        "dbmdz/bert-large-cased-finetuned-conll03-english", use_cdn=False
    )
    tokenizer = AutoTokenizer.from_pretrained("bert-base-cased", use_cdn=False)
    nlp = pipeline(
        "ner", model=model, tokenizer=tokenizer, grouped_entities=True
    )

    log_fmt = (
        "[%(asctime)s %(levelname)-8s], [%(filename)s:%(lineno)s - "
        + "%(funcName)s()], %(message)s"
    )
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    here = os.path.dirname(os.path.abspath(__file__))
    c_dir = os.path.join(here, "test_data")

    ner_dict = defaultdict(set)
    for text in ner_dir(c_dir):
        print(nlp(text))
