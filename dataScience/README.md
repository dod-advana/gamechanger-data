# GC - Machine Learning

## Rules for dataScience repo

- Everything in dataScience/src should be independent of things outside of that structure (should not need to import from dataPipeline, common, etc).
- Where ever possible, code should be modular and broken down into smallest logical pieces and placed in the most logical subfolder.
- Include README.md file and/or example scripts demonstrating the functionality of your code.
- Models should not be stored on Bitbucket.
- Data should not be stored on Bitbucket, there is a script in the `dataScience/scripts` folder to download a corpus from s3.
- File paths in dataScience/configs config files should be relative to dataScience and only used for local testing purposes (feel free to change on your local machine, but do not commit to repo with system specific paths).
- A config should not be required as an input parameter to a function; however a config can be used to provide parameters to a function (`foo(path=Config.path)`, rather than `foo(Config)`).
- If a config is used for a piece of code (such as training a model), the config should be placed in the relevant section of the repo (dataPipeline, api, etc.) and should clearly designate which environment the config is for (if relevant).

## Structure of the Repo:

1. `configs` - Files that can be used in conjunctino with test/example scripts

2. `data` - An empty folder that you can use to download and store data for local testing.  Should not upload any contents to repo.

3. `models` - An empty folder that you can use for local testing and running of models.  Should not upload any contents to repo.

4. `scripts` - Scripts that demostrate the functionality of code from `src`.

5. `src` - Classes and methods that will be used by other GameChanger modules outside the dataScience Repo.

6. `unittest` - Unit tests for code in `src`.


## HOW TO:
### Train models locally
1. `. dataScience/setup_env.sh`
2. `python -m dataScience.scripts.run_train_models --flag {MODEL_NAME_SUFFIX} --saveremote {True or False} --model_dest {FILE_PATH_MODEL_OUTPUT} --corpus {CORPUS_DIR}`

### Run Flask App and Transformer App in Docker
1. place transformer_cache (unzipped) at root dir `gamechanger/`
2. `source ./dataScience/setup_env.sh DEV`
3. `cd dataScience/api`
4. `docker-compose build`
5. `docker-compose up`

if you are on mac, at step 2, user DEVLOCAL instead of DEV
if this is a PROD env, use PROD

### Train Models in Docker
1. `cd dataScience`
2. CONFIGURE docker-compose.yml:
  + set `-s` True to save remote.
  + set `-v` True or False to run assessment
  + set `-d` for directory output for models (suggest to  leave default to dataScience/models) 
  + set `x` for experiment name, otherwise each run is separate experiment
3. `docker-compose build`
4. `docker-compose up` 
  + `docker-compose up -d` use if you want to distach the logs.
5. Once training is done, gc-ml-train container exits.
  + check `localhost:5050` (mlflow UI) that your model info is there.
6. (optional) change params in config, repeat step 3/4a for retrain.

- saves model locally in dataScience/models/
- requires corpus
- requires rebuild if changing code
- remember to configure docker-compose.train.yml

