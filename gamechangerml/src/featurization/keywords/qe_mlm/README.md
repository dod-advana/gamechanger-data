# Context-Aware Query Expansion

This is an adaptation of Victor Dibia's CQE algorithm. A complete
description can be found on [Arxiv](https://arxiv.org/abs/2007.15211).

## Language Models
Two language models are used, one from spaCy and one from Hugging Face.

The recommended spaCy model is `en-core-web-md`. Generally, the spaCy model
must have the processing components `["tagger", "ner"]`. See the
[spaCy documentation](https://spacy.io/models/en) for model downloads.

The default Hugging Face model is [`"bert-base-uncased"`](https://huggingface.co/transformers/pretrained_models.html).
If this model is not present on your system it will be downloaded and
saved on the first instantiation of this class.

## Usage
See the `example/` directory for a runnable example, *viz.*,

```
>>> from pprint import pprint
>>> import spacy
>>> from qe_mlm.qe import QeMLM
>>>
>>> nlp = spacy.load("en_core_web_md")
>>> qe = QeMLM(nlp, model_path="bert-base-uncased")
>>>
>>> query = "Find a book, painting, or work of art created in Santa Monica or on the west coast"
result = qe.predict(query, threshold=0.2, top_n=2)
>>> print(result)
['sculpture', 'piece']
>>> pprint(qe.explain, indent=2)
{ 'expansions': [ { 'ent_desc': None,
                    'expansion': None,
                    'named_entity': '',
                    'pos': 'VERB',
                    'pos_desc': 'verb',
                    'token': 'Find',
                    'token_index': 0},
                  { 'ent_desc': None,
                    'expansion': None,
                    'named_entity': '',
                    'pos': 'DET',
                    'pos_desc': 'determiner',
                    'token': 'a',
                    'token_index': 1},
                  { 'ent_desc': None,
                    'expansion': [ { 'probability': 0.8155179023742676,
                                     'token': 'sculpture'},
                                   { 'probability': 0.11150502413511276,
                                     'token': 'drawing'}],
                    'named_entity': '',
                    'pos': 'NOUN',
                    'pos_desc': 'noun',
                    'token': 'book',
                    'token_index': 2},
                  { 'ent_desc': None,
                    'expansion': None,
                    'named_entity': '',
                    'pos': 'PUNCT',
                    'pos_desc': 'punctuation',
                    'token': ',',
                    'token_index': 3},
                  { 'ent_desc': None,
                    'expansion': [ { 'probability': 0.2674008011817932,
                                     'token': 'film'},
                                   { 'probability': 0.08297424018383026,
                                     'token': 'magazine'}],
                    'named_entity': '',
                    'pos': 'NOUN',
                    'pos_desc': 'noun',
                    'token': 'painting',
                    'token_index': 4},
                  { 'ent_desc': None,
                    'expansion': None,
                    'named_entity': '',
                    'pos': 'PUNCT',
                    'pos_desc': 'punctuation',
                    'token': ',',
                    'token_index': 5},
                  { 'ent_desc': None,
                    'expansion': None,
                    'named_entity': '',
                    'pos': 'CCONJ',
                    'pos_desc': 'coordinating conjunction',
                    'token': 'or',
                    'token_index': 6},
                  { 'ent_desc': None,
                    'expansion': [ { 'probability': 0.582930862903595,
                                     'token': 'piece'},
                                   { 'probability': 0.30685243010520935,
                                     'token': 'work'}],
                    'named_entity': '',
                    'pos': 'NOUN',
                    'pos_desc': 'noun',
                    'token': 'work',
                    'token_index': 7},
                  { 'ent_desc': None,
                    'expansion': None,
                    'named_entity': '',
                    'pos': 'ADP',
                    'pos_desc': 'adposition',
                    'token': 'of',
                    'token_index': 8},
                  { 'ent_desc': None,
                    'expansion': [ { 'probability': 0.847743570804596,
                                     'token': 'art'},
                                   { 'probability': 0.1328895539045334,
                                     'token': 'fiction'}],
                    'named_entity': '',
                    'pos': 'NOUN',
                    'pos_desc': 'noun',
                    'token': 'art',
                    'token_index': 9},
                  { 'ent_desc': None,
                    'expansion': None,
                    'named_entity': '',
                    'pos': 'VERB',
                    'pos_desc': 'verb',
                    'token': 'created',
                    'token_index': 10},
                  { 'ent_desc': None,
                    'expansion': None,
                    'named_entity': '',
                    'pos': 'ADP',
                    'pos_desc': 'adposition',
                    'token': 'in',
                    'token_index': 11},
                  { 'ent_desc': 'Countries, cities, states',
                    'expansion': None,
                    'named_entity': 'GPE',
                    'pos': 'PROPN',
                    'pos_desc': 'proper noun',
                    'token': 'Santa',
                    'token_index': 12},
                  { 'ent_desc': 'Countries, cities, states',
                    'expansion': None,
                    'named_entity': 'GPE',
                    'pos': 'PROPN',
                    'pos_desc': 'proper noun',
                    'token': 'Monica',
                    'token_index': 13},
                  { 'ent_desc': None,
                    'expansion': None,
                    'named_entity': '',
                    'pos': 'CCONJ',
                    'pos_desc': 'coordinating conjunction',
                    'token': 'or',
                    'token_index': 14},
                  { 'ent_desc': None,
                    'expansion': None,
                    'named_entity': '',
                    'pos': 'ADP',
                    'pos_desc': 'adposition',
                    'token': 'on',
                    'token_index': 15},
                  { 'ent_desc': 'Non-GPE locations, mountain ranges, bodies of '
                                'water',
                    'expansion': None,
                    'named_entity': 'LOC',
                    'pos': 'DET',
                    'pos_desc': 'determiner',
                    'token': 'the',
                    'token_index': 16},
                  { 'ent_desc': 'Non-GPE locations, mountain ranges, bodies of '
                                'water',
                    'expansion': None,
                    'named_entity': 'LOC',
                    'pos': 'PROPN',
                    'pos_desc': 'proper noun',
                    'token': 'west',
                    'token_index': 17},
                  { 'ent_desc': 'Non-GPE locations, mountain ranges, bodies of '
                                'water',
                    'expansion': None,
                    'named_entity': 'LOC',
                    'pos': 'PROPN',
                    'pos_desc': 'proper noun',
                    'token': 'coast',
                    'token_index': 18}],
  'query': [ 'Find',
             'a',
             'book',
             ',',
             'painting',
             ',',
             'or',
             'work',
             'of',
             'art',
             'created',
             'in',
             'Santa',
             'Monica',
             'or',
             'on',
             'the',
             'west',
             'coast'],
  'terms': [ {'probability': 0.8155179023742676, 'token': 'sculpture'},
             {'probability': 0.2674008011817932, 'token': 'film'},
             {'probability': 0.582930862903595, 'token': 'piece'}]}
>>>
```
## Acknowledgment
Thanks are due to Victor Dibia of Cloudera for his help, and early code.

## License
MIT License
&copy; 2020 Victor Dibia, Chris Skiscim

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.


