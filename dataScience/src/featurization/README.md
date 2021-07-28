## Summary

In summary.py, to generate the summaries for documents the documents are first cleaned. Excessive punctuation, list indicators, websites, phrases in parenthesis and particularly short paragraphs are all removed from the text before being passed to the gensim summarizer function. The idea is that this gets rid of less important content, so that it is not considered in the summary. The gensim summarizer uses TextRank to generate summaries. When the text is particularly large it is separated into chunks to develop summaries for each chunk and when that summary gets to be long the summary itself is summarized using gensim. Lastly excess whitespace is removed from the resulting summaries so they appear more visually appealing.

Areas for improvement include adjusting how larger texts are being handled and also adding a large text handler to the key words. Additionally, adding preprocessing methods if various seemingly irrelevant pieces of information are captured in summaries. Lastly, if there is a way to use the table of contents or statement of purpose to extract more specific summaries even with different file formats.

## Abbreviations

In abbreviation.py there is a function that uses a dictionary of abbreviations to identify abbreviations contained within the document. It replaces all the abbreviations with their expanded form and returns the updated text and a dictionary with the abbreviations contained within the text and their expansion in the document.

Additionally there is a function to add abbreviations and their expansions to the current dictionary as we find other abbreviations that need to be identified.

## HuggingFace test
test_hf_ner.py tests the HuggingFace NER using the test data. TODO: format output, add timing to both to see the difference between spacy speed and HF speed (though spacy seems to be much much faster)
