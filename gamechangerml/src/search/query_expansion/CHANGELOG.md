## Sprint 80 `feature/UOT-77456`

### `build_qe_model.py`
- Remove empty page warnings; produce various counts and report these at termination.

- Change default `ngram` range CLI argument to `(1, 2)`.

- Change the `num_keywords` CLI argument default to 2.

- Add a mandatory `--word-wt` CLI argument to specify which language model to use
in the SIF algorithm. The recommended model is

```
gamechangerml/src/search/query_expansion/aux_data/word-freq-corpus-20201101.txt
```

- This is our domain-specific language model. In this model, words with
frequency `>= 50` are included. Previously, we were using 

```
gamechangerml/src/search/query_expansion/aux_data/enwiki_vocab_min200.txt
```
- **NB**: The updated `usage` is

```
usage: python build_qe_model.py [-h] -c CORPUS_DIR -i INDEX_DIR [-t NUM_TREES]
                                [-k NUM_KEYWORDS] -w WORD_WT_FILE -g NGRAM -a
                                ABBRV_FILE

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
  -w WORD_WT_FILE, --word-wt WORD_WT_FILE
                        path + name of the word weight file in aux_data/
  -g NGRAM, --ngram NGRAM
                        tuple of (min, max) length of keywords to find
  -a ABBRV_FILE, --abbrv-file ABBRV_FILE
                        path and file for the short-form to long-form
                        abbreviation mapping (unused, not required)

```


- Create a two-pass technique to creating embeddings for abbreviations and add them to
the `spaCy` language model. Integration, testing, and documentation is pending.

- Create a single pass method for embedding document titles to their corresponding
 document identifiers (*e.g.*, DoDI 1000.1). These will be added to the `spaCy` language
model.

- Add a custom JSON encoder for `numpy` objects. The abbreviation and document title
embeddings will be stored at termination of `build_qe_model.py`. When the `QE` class is
instantiated, these embeddings will be added to the `spaCy` language model.

### `qe.py`
- Add `strict` argument to `sif_embedding()`; if `True` *any* OOV token will 
abandon the expansion term and return a zero vector. This is to insure mangled words are
not in the `annoy` index.

- Correct a bug in `sif_alg` to insure proper *L2* normalization of the weighted, averaged vector.

- Add a `threshold` argument to the `expand()` method. `annoy` returns the angular distance
between two vectors with domain = [-1, 1]. This is mapped to the cosine domain = [0, 1].
Any candidate expansion term whose cosine `< threshold` is rejected as an expansion term.
This is to further the goal of having better quality expansion terms. The default value is
`threshold=0.2`.

- Reduce the `spaCy` footprint by using `get_lg_vectors()`. This disables the pipeline
components `["ner", "parser", "tagger"]` as this are not needed. In particular, the `ner`
pipeline component consumes a large amount of memory. Overall efficiency is thus improved.

- **NB**: The signature for the `expand()` method has changed to the following (note the
`threshold=0.2` now applies to both the `method="emb"` and `method="mlm"'):
```
    def expand(self, query_str, topn=2, threshold=0.2, min_tokens=3):
        """
        Expands a query string into the `topn` most similar terms excluding
        the tokens in `query_str`. If a token does not have an embedding,
        it is not added to the embedding matrix.

        Args:
            query_str (str): query string

            topn (int): number of most similar terms

            threshold (float): if the method is "mlm", the softmax probability
                must be > threshold for a word to included in the expansion;
                if the method is "emb", this applies to the cosine distance.

            min_tokens (int): if the method is "mlm", the number of tokens in
                the `query_str` must be > `min_tokens`; this value is ignored
                if `method="emb"`.

        Returns:
            list of up to `topn` most similar terms if an embedding exists
                for `query_str`. Empty list indicates no expansion terms are
                available.

        """
```

- Update `README.md`; bump version.

### `query_expansion_example.py`
- The CLI options were expanded to take a flat file for running queries through
an existing model. It will report out-of-vocabulary tokens in the expansion terms
and query strings with no expansion.

- The usage is

```
usage: query_expansion_example.py [-h] -i INDEX_DIR -q QUERY_FILE

python query_expansion_example.py

optional arguments:
  -h, --help            show this help message and exit
  -i INDEX_DIR, --index-dir INDEX_DIR
                        ANN index directory
  -q QUERY_FILE, --query-file QUERY_FILE
                        text file containing one sample query per line
```

### `pytest`
Tests were updated to reflect the changed APIs.

```
| => py.test -v gamechangerml/src/search/query_expansion/tests
==================================================== test session starts ====================================================
platform darwin -- Python 3.6.8, pytest-6.0.1, py-1.9.0, pluggy-0.13.1 -- /Users/chrisskiscim/Envs/python3/bin/python3
cachedir: .pytest_cache
rootdir: /Users/chrisskiscim/projects/gamechanger/repo/gamechanger, configfile: pytest.ini
plugins: cov-2.9.0, profiling-1.3.0, typeguard-2.9.1
collected 9 items

gamechangerml/src/search/query_expansion/tests/test_qe.py::test_qe_emb_expand PASSED                                    [ 11%]
gamechangerml/src/search/query_expansion/tests/test_qe.py::test_qe_emb_empty PASSED                                     [ 22%]
gamechangerml/src/search/query_expansion/tests/test_qe.py::test_qe_emb_oov_1 PASSED                                     [ 33%]
gamechangerml/src/search/query_expansion/tests/test_qe.py::test_qe_emb_iv_2 PASSED                                      [ 44%]
gamechangerml/src/search/query_expansion/tests/test_qe.py::test_qe_mlm[args0] PASSED                                    [ 55%]
gamechangerml/src/search/query_expansion/tests/test_qe.py::test_qe_mlm[args1] PASSED                                    [ 66%]
gamechangerml/src/search/query_expansion/tests/test_qe.py::test_qe_mlm[args2] PASSED                                    [ 77%]
gamechangerml/src/search/query_expansion/tests/test_qe.py::test_qe_mlm[args3] PASSED                                    [ 88%]
gamechangerml/src/search/query_expansion/tests/test_qe_exceptions.py::test_qe_except_build PASSED                       [100%]

==================================================== 9 passed in 32.86s =====================================================
```

### Testing with user query history
To insure no errant expansions are returned, `query_expansion_example.py` was run
with the client-supplied query history files:

```
gamechangerml/src/search/query_expansion/tests/test_data/query_12_10_2020_a.txt
gamechangerml/src/search/query_expansion/tests/test_data/query_12_10_2020_b.txt
```

This represents 9,266 user query strings. Each expansion term was tokenized via
`spaCy` and its embedding vector was retrieved. If the embedding vector was all
zero, *i.e*, `np.all(v == 0.0)` is `True`, the token is counted as Out-of-Vocabulary (OOV).
In addition, there are user queries for which there is no expansion due to the `threshold`
not being satisfied.

The results were

```
[2020-12-11 07:56:34,051 INFO    ], [query_expansion_example.py:95 - <module>()],  num OOV expansion terms out of 5,324 examples :     0
[2020-12-11 07:56:34,051 INFO    ], [query_expansion_example.py:96 - <module>()],                query strings with no expansion : 1,452

[2020-12-11 07:57:46,441 INFO    ], [query_expansion_example.py:95 - <module>()],  num OOV expansion terms out of 3,942 examples :     0
[2020-12-11 07:57:46,441 INFO    ], [query_expansion_example.py:96 - <module>()],                query strings with no expansion : 1,056
```

### Known Issues in `qe.py`
In tests using actual user queries, there are instances where an expansion term
is identical to the query string, *e.g.*,

```
'Sexual Assault' -> ['sexual assault', 'sexual harassment']
```

This is under investigation. Most likely the problem lies in `build_qe_model.py` or its
supporting modules. These are not widespread. 
For the most part, this is harmless with respect to the 
keyword search.

Document numbers are still a bit problematic, *e.g.*,

```
DoDI 4500 -> ['dodi 4000', 'dodi 6000']
```

This will be addressed in a subsequent version.