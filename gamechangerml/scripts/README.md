# Scripts for Training and Testing model functionality

---

The scripts contained in this folder can be used to train new Doc2Vec models, as well as test the 
functionality of models.  Please follow the steps below to utilize the scripts.

### manually_train_models.py

**Script Notes:** This script will train a co-occurance based phrase detector 
using Gensim's `Phraser`, as well as a Doc2Vec model using a wrapper around Gensim's Doc2Vec 
implementations.  The models will be trained using `.json` files located in the `Config.CORPUS_DIR` and 
saved in the `Config.MODEL_DIR` which can be defined in the `gamechangerml/src/modelzoo/semantic/D2V_Config.py`.

### using_existing_models.py

**Script Notes:** In the script specifiy the `model_dir` as well as the specific `model_name` and this 
script will load in the phrase detector models, as well as the Doc2Vec model and run a couple of inferences.

### query_expansion_example.py

**Script Notes:** This is commandline application (CLI) that demonstrates query expansion. You will
need to build an index in order to run this example. Details on how that is accomplished can be
found in `src/search/query_expansion/README.md`. 

Usage for this script is
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

### entity_extraction_example.py

**Script Notes:** NB Experimental. This is a commandline application (CLI) demonstrating named
entity recognition (NER) using either the [spaCy](https://spacy.io/usage/linguistic-features#named-entities) NER or 
the [Hugging Face transformers](https://github.com/huggingface/transformers) NER. Usage for this script
is
```
usage: entity_extraction_example.py [-h] -m {spacy,hf} [-c CORPUS_DIR]

Example Named Entity Extraction (NER)

optional arguments:
  -h, --help            show this help message and exit
  -m {spacy,hf}, --method {spacy,hf}
  -c CORPUS_DIR, --corpus-dir CORPUS_DIR
                        corpus directory
```
Entities of type ORG (organization) and LAW (legal) are extracted using spaCy. `hf` extracts type
ORG entities.

### There are other scripts present--for now they can be ignored
