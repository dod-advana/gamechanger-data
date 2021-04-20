# embed-reader
This package implements a transformer-based method for finding answers to user queries
in a set of text passages. In this context, transformer is called a *Reader*. In Gamechanger, the 
passages are the paragraphs retrieved by Elasticsearch for a user's query.

The "workflow" is 
> *user query* -> *Elasticsearch* -> *Reader* -> *UI*

The underlying modeling is Question-Answer. The query can be as natural as
> What is the policy on telework?

Or it can be an informational type query, such as
> telework policy

Each of these are interpreted in a different way and may yield different results.
That's the whole point of this approach.

## Update Your Environment !
The requirements are
- `torch==1.5.1`
- `torchvision==0.6.1`
- `transformers==3.1.0`

## About the Models
Instantiating the `SparseReader` class requires a `model_name`. The following models
have been tested and are sufficient for our application:

1. deepset/bert-large-uncased-whole-word-masking-squad2
2. distilbert-base-uncased-distilled-squad
3. deepset/bert-base-cased-squad2
4. bert-large-uncased-whole-word-masking-finetuned-squad

Models 1 and 4 provide the most accurate and rich results. It is also the slowest to load,
and run. Model 2 is the fastest to load and run, however, the results may not be very good. I
recommend Model 2 for testing.

### Getting the Models
When instantiating the `SparseReader` class with one of the model names, `transformers`
will try to find the required model files on your machine. If they do not exist, `transformers`
will attempt to download the required model files. Some of these are very large, so be patient.

An alternative is to use the [Hugging Face](https://huggingface.co/models) download
site. Search for the model names above and you will be taken to its page. Near the
bottom of the page, there is code you can copy, verbatim, and run. This will perform
the download.

By default, all model files are written to `~/.cache/transformers`.

**WARNING !**
> ZScaler may block the downloads and the library will raise an `OSError`. You will
> need to contact the HelpDesk and ask for a ZScaler policy exception. This may
> take time to put into effect.

## Example Notebooks
These are located in `embed_reader/examples`. These demonstrate each of the four models.
Running these is the best way to see it all in action.

## Usage
```
sparse_reader = SparseReader(model_name="distilbert-base-uncased-distilled-squad")
```
The class takes two additional arguments, with the defaults shown below. These
should not be changed. Setting `use_gpu=True` will raise a `NotImplementedError`.

**Example**
```
sparse_reader = SparseReader(
    model_name="distilbert-base-uncased-distilled-squad",
    context_window_size=150,
    use_gpu=False,
)
```

### Using the `predict` Method
```
results = sparse_reader(query_results, top_k=None)
```
`query_results` is a dictionary holding the original user query string - this is the raw string with no
query expansion terms. The paragraph text and document ID resulting from the
Elasticsearch query are also included (see the example below).

**The character length of the paragraph should >= 75 characters. `SparseReader` does not 
check the lengh and does not perform any manipulation of the query text or the paragraph text.**

This provides sufficient context for the underlying model. The 75 character was chosen after
limited experimentation. It is the responsibility of the caller to enforce the character length.

`top_k`, `(int|None)` allows the caller to specify a subset of the query results to be
returned. The default is `top_k=None` and this will effect a re-ranking of the input.

**Further re-ranking is not advised.**

`results` will be returned in ranked order as determined by an internal scoring function.

#### `results` Output Example
```
{
  "query": "Telework Policy",
  'answers': [
    {'answer': 'telework is permitted in cirumstances',
      'context': 'telework is permitted in cirumstances...',
      'id': 'DoDI 1234 All about Telework_0_12.pdf',
      'text': 'telework is permitted in cirumstances...'},
    {'answer': 'Working from home',
      'context': 'Working from home, or telework is referred to as...',
      'id': "DoDD 8484 What's Up With Telework_5_6.pdf",
      'text': 'Working from home, or telework is referred to as...'}
    ]
}
 

```
Because the underlying model is a pre-trained Question-Answer model, an `"answer"` is
provided. The `"context"` is the passage that best supports the `"answer"`. The `context` is a
fixed number of characters (`context_window_size`). There is no guarantee that the
`context` will either start or end on a word boundary.
