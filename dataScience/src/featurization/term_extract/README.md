## term_extract

This extracts *n*-grams using parts-of-speech. The excellent `spaCy` [Matcher API](https://spacy.io/usage/rule-based-matching) 
is used for quick extraction. The intent is to organize these terms for use in query suggestion.

The patterns of interest are *n*-grams (*1 < n < 5*) of NOUN, ADJ as shown below:
```python
noun, adj, prep = (
        {"POS": "NOUN", "IS_PUNCT": False},
        {"POS": "ADJ", "IS_PUNCT": False},
        {"POS": "DET", "IS_PUNCT": False},
    )

    patterns = [
        [adj],
        [{"POS": {"IN": ["ADJ", "NOUN"]}, "OP": "*", "IS_PUNCT": False}, noun],
        [
            {"POS": {"IN": ["ADJ", "NOUN"]}, "OP": "*", "IS_PUNCT": False},
            noun,
            prep,
            {"POS": {"IN": ["ADJ", "NOUN"]}, "OP": "*", "IS_PUNCT": False},
            noun,
        ],
    ]
```
For example, if the the text is *This is a technical phrase*, the extracted bigram is *technical phrase*.

## Usage
To output prefixed-organized bigrams from the GameChanger corpus using the key `"text"`:
```python
term_extract = TermExtractor(max_term_length=2, min_freq=2, ner=False)
output_dict = term_extract.count_from_dir(data_dir="some/path/to/json/corpus/")
```
A snippet of the output dictionary would look like
```python
[{'input': '"federal register', 'weight': 2},
 {'input': 'absentee ballot', 'weight': 10},
 {'input': 'absentee ballots', 'weight': 7},
 {'input': 'absentee registration', 'weight': 2}
]
```
where `input` is the extracted term and `weight` is the occurrence frequency.

For single document extraction:
```python
term_extract = TermExtractor(max_term_length=2, min_freq=2, ner=False)
output_dict = term_extract.count_from_document("your string here")
```
In this case, a [Counter](https://docs.python.org/3/library/collections.html#collections.Counter) object is 
returned for all pattern-matched bigrams.
