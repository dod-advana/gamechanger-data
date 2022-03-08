import re
from string import punctuation

punct = set(punctuation)

def utf8_pass(text):
    return text.encode("utf-8", "ignore").decode("utf-8")


def clean_text(doc_text: str) -> str:
    """
    The text is cleaned from special characters and extra spaces
    Args:
        doc_text: input text to be cleaned

    Returns:

    """

    text = doc_text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    remove = punctuation + "”“"
    remove = remove.replace(".", "")

    text = text.translate({ord(i): None for i in remove})

    return text

