# GC - Machine Learning
## Table of Contents
1. [Directory](##Directory)
2. [Development Rules](#Development-Rules)
3. [Train Models](#Train-Models)
4. [ML API](#ML-API)

## Directory
```
dataScience
├── api
│   ├── fastapi
│   └── utils
├── configs
├── data
├── experimental
│   ├── notebooks
│   │   ├── evaluation
│   │   ├── portion_marking_demo
│   │   └── sentence-transformer
│   └── policy
│       └── text_classif
│           ├── configuration
│           ├── examples
│           └── utils
├── mlflow
├── models
│   ├── qexp_*
│   ├── sent_index_*
│   ├── topic_models
│   └── transformers
├── scripts
├── src
│   ├── featurization
│   │   ├── data
│   │   ├── keywords
│   │   │   └── qe_mlm
│   │   ├── term_extract
│   ├── model_testing
│   ├── search
│   │   ├── QA
│   │   ├── embed_reader
│   │   ├── evaluation
│   │   ├── query_expansion
│   │   ├── ranking
│   │   ├── semantic
│   │   └── sent_transformer
│   ├── text_handling
│   │   └── assets
│   └── utilities
│       └── numpy_encoder
├── train
│   └── scripts
└── unittest
```

## Development Rules
- Everything in dataScience/src should be independent of things outside of that structure (should not need to import from dataPipeline, common, etc).
- Where ever possible, code should be modular and broken down into smallest logical pieces and placed in the most logical subfolder.
- Include README.md file and/or example scripts demonstrating the functionality of your code.
- Models/large files should not be stored on Github.
- Data should not be stored on Github, there is a script in the `dataScience/scripts` folder to download a corpus from s3.
- File paths in dataScience/configs config files should be relative to dataScience and only used for local testing purposes (feel free to change on your local machine, but do not commit to repo with system specific paths).
- A config should not be required as an input parameter to a function; however a config can be used to provide parameters to a function (`foo(path=Config.path)`, rather than `foo(Config)`).
- If a config is used for a piece of code (such as training a model), the config should be placed in the relevant section of the repo (dataPipeline, api, etc.) and should clearly designate which environment the config is for (if relevant).


## Train Models
1. Setup your environment, and make any changes to configs: 
- `source ./dataScience/setup_env.sh DEV`
2. Ensure your AWS enviroment is setup (you have a default profile)
3. Get dependencies
- `source ./dataScience/scripts/download_dependencies.sh`
4. For query expansion:
- `python -m dataScience.train.scripts.run_train_models --flag {MODEL_NAME_SUFFIX} --saveremote {True or False} --model_dest {FILE_PATH_MODEL_OUTPUT} --corpus {CORPUS_DIR}`
5. For sentence embeddings:
- `python -m dataScience.train.scripts.create_embeddings -c {CORPUS LOCATION} --gpu True --em msmarco-distilbert-base-v2`

## ML API
1. Setup your environment, make any changes to configs: 
- `source ./dataScience/setup_env.sh DEV`
2. Ensure your AWS enviroment is setup (you have a default profile)
3. Dependencies will be automatically downloaded and extracted.
4. `cd dataScience/api`
5. `docker-compose build`
6. `docker-compose up`
7. visit `localhost:5000/docs`

## FAQ
- Do I need to train models to use the API?
  - No, you can use the pretrained models within the dependencies. 
- The API is crashing when trying to load the models.
  - Likely your machine does not have enough resources (RAM or CPU) to load all models. Try to exclude models from the model folder.
- Do I need a machine with a GPU?
  - No, but it will make training or inferring faster.
- What if I can't download the dependencies since I am external?
  - We are working on making models publically available. However you can use download pretrained transformers from HuggingFace to include in the models/transformers directory, which will enable you to use some functionality of the API. Without any models, there is still functionality available like text extraction avaiable. 
