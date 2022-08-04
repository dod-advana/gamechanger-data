# Embedding-based Query Expansion (QE)

---

Query expansion (QE) is used to find words and phrase that are similar to a given query string. Since
the expansion terms are taken from the corpus, it tends makes search more efficient in returning
relevant text.

For example, if the query string is *sole source contract*, an expanded query might include
`['sole source', 'sole-source basis']`.

The algorithm here uses word and phrase embeddings as the basis for an initial similarity search.
`QE` uses [spaCy's](https://spacy.io/) `en-core-web-lg` model to access [GloVe](https://nlp.stanford.edu/projects/glove/)
embeddings for single words (tokens). 

Key-phrases are found using the 
[Rapid Automatic Keyword Extraction](https://www.researchgate.net/publication/227988510_Automatic_Keyword_Extraction_from_Individual_Documents) 
or RAKE algorithm. To create a fixed-length embedding from multiple words, a simplified version
of the [Smoothed Inverse Freqnecy](https://openreview.net/forum?id=SyK00v5xx) (SIF) algorithm.

Since all the embedding vectors are *L2* normalized, the similarity (cosine) can be found via a dot product. However,
searching for a set of vectors with the highest similarity to a given vector does not scale well. To overcome this,
we use an [Approximate Nearest Neighbor](https://cims.nyu.edu/~regev/toc/articles/v008a014/v008a014.pdf) search. As of
this writing, the [annoy](https://github.com/spotify/annoy) package is used.

See `CHANGELOG.md` for the most up-to-date information.

## Getting Started
The requirements are:
```
annoy==1.16.3
https://github.com/explosion/spacy-models/releases/download/en_core_web_lg-2.3.1/en_core_web_lg-2.2.5.tar.gz
spacy==2.2.4
```

First install `spacy`
```
pip install spacy==2.2.4
```
Then install the `spacy` language model
```
python -m spacy download en_core_web_lg 
```
`annoy` can be installed at any point as it does not depend on `spacy`
```
pip install annoy==1.16.3
```

I recommend checking your `spacy` installation using `spacy validate`. From the command line on my system, 
it produces
```
| => spacy validate
✔ Loaded compatibility table

====================== Installed models (spaCy v2.2.4) ======================
ℹ spaCy installation:
/Users/chrisskiscim/Envs/python3/lib/python3.6/site-packages/spacy

TYPE      NAME                             MODEL                            VERSION
package   en-trf-xlnetbasecased-lg         en_trf_xlnetbasecased_lg         2.2.0   ✔
package   en-trf-robertabase-lg            en_trf_robertabase_lg            2.2.0   ✔
package   en-trf-distilbertbaseuncased-lg   en_trf_distilbertbaseuncased_lg   2.2.0   ✔
package   en-trf-bertbaseuncased-lg        en_trf_bertbaseuncased_lg        2.2.0   ✔
package   en-core-web-sm                   en_core_web_sm                   2.2.5   ✔
package   en-core-web-md                   en_core_web_md                   2.2.5   ✔
package   en-core-web-lg                   en_core_web_lg                   2.2.5   ✔
package   de-trf-bertbasecased-lg          de_trf_bertbasecased_lg          2.2.0   ✔
```
Incompatible language models will be flagged. Note that the language models are
full-fledged Python packages and can be imported. See the [spaCy documentation](https://spacy.io/models/en)
for more information.

## Building the Index
Both an index and vocabulary file **must** be built for query expansion to work. 
A command line utility, `build_qe_models.py` is provided in the directory `/build_ann_cli`.

 
Usage is as follows
```
usage: python build_qe_model.py [-h] -c CORPUS_DIR -i INDEX_DIR [-t NUM_TREES]
                                [-k NUM_KEYWORDS] [-w WEIGHT_FILE] -g NGRAM
                                [-a ABBRV_FILE] [-m]

optional arguments:
  -h, --help            show this help message and exit
  -c CORPUS_DIR, --corpus-dir CORPUS_DIR
                        directory of document corpus; default=Config.DATA_DIR
  -i INDEX_DIR, --index-dir INDEX_DIR
                        directory for saving the index;
                        default=Config.MODEL_DIR
  -t NUM_TREES, --num-trees NUM_TREES
                        number of trees in the index; default=125
  -k NUM_KEYWORDS, --num-keywords NUM_KEYWORDS
                        number of keywords per page to add to the index,
                        default=3
  -w WEIGHT_FILE, --word-wt WEIGHT_FILE
                        path + name of the word weight file in aux_data/
  -g NGRAM, --ngram NGRAM
                        tuple of (min, max) length of keywords to find
  -a ABBRV_FILE, --abbrv-file ABBRV_FILE
                        path and file for the short-form to long-form
                        abbreviation mapping
  -m, --merge-word-sim  Whether or not the word sim (wiki-news-300d-1M.vec)
                        results should be concatenated to the annoy index
```
Documents are processed on a page-by-page basis using the raw text of the page. The only pre-processing that is
performed is to replace newline characters with a single space and reduce inter-word spacing to
a single space.

Two files are produced. The index is prefixed with `ann-index_` with extension `.ann`. The file name
holds the timestamp of its creation date and time. Similarly, the vocabulary file is prefixed with
`ann-index-vocab_` and suffixed with `.pkl` and has a timestamp of its creation date and time. These
timestamps will be the same.

## Running the tests
`pytest` tests are in the `tests/` directory with a small set (3) of documents in `test/test_data`. To
run the `qe` tests, from the top level directory `gamechanger/`
```
py.test -v -k test_qe
```
or
```
python -m pytest -v -k test_qe
```

If it all goes well, you'll see something like
```
==================================================== test session starts ====================================================
platform darwin -- Python 3.7.3, pytest-6.0.1, py-1.9.0, pluggy-0.13.1 -- /Envs/gc/bin/python
cachedir: .pytest_cache
rootdir: /gamechanger/repo/gamechanger
plugins: cov-2.9.0, typeguard-2.9.1
collected 21 items / 16 deselected / 5 selected

gamechangerml/src/modelzoo/query_expansion/tests/test_qe_basic.py::test_qe_expand PASSED                                [ 20%]
gamechangerml/src/modelzoo/query_expansion/tests/test_qe_basic.py::test_qe_empty PASSED                                 [ 40%]
gamechangerml/src/modelzoo/query_expansion/tests/test_qe_basic.py::test_qe_oov_1 PASSED                                 [ 60%]
gamechangerml/src/modelzoo/query_expansion/tests/test_qe_basic.py::test_qe_oov_2 PASSED                                 [ 80%]
gamechangerml/src/modelzoo/query_expansion/tests/test_qe_exceptions.py::test_qe_except_build PASSED                     [100%]

===================================================== warnings summary ======================================================
dataPipelines/tests/test_server.py:5
  /gamechanger/dataPipelines/tests/test_server.py:5: PytestUnknownMarkWarning: Unknown pytest.mark.dev - is this a typo?  You can register custom marks to avoid this warning - for details, see https://docs.pytest.org/en/stable/mark.html
    @mark.dev

-- Docs: https://docs.pytest.org/en/stable/warnings.html
```

Please open an issue if you encounter a failure.

