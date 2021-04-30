from dataScience.models.topic_models.tfidf import tfidf_model
from dataScience.src.text_handling.process import topic_processing


def extract_topics(doc_dict):
    doc_dict["topics_rs"] = {}

    topics = tfidf_model.get_topics(
        topic_processing(doc_dict["text"], bigrams), topn=5)
    for score, topic in topics:
        topic = topic.replace('_', ' ')
        doc_dict["topics_rs"][topic] = score

    return doc_dict
