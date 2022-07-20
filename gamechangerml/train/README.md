# GC ML TRAIN
## How to use pipeline.py
```
from gamechangerml.train.pipeline import Pipeline
train = Pipeline()
# load in params or set to config file
params= {'corpus':"gamechangerml/corpus", "upload":True, "version":"v9"}
# run a part of the pipeline
train.run(build_type = "qexp", run_name="20210810", params=params)
# run a different part of the pipeline
train.run(build_type = "sentence", run_name="20210810", params=params)
```
Above will build the component, compress, and upload it to s3 (if available)
Available build_types:
- metadata
- qexp
- sentence
## How to use docker
- inside gamechangerml/train
- `docker-compose up`
## MLFlow
- MLFlow in development is hosted on http://10.194.9.119:5050
- BEFORE running trainings: `export MLFLOW_TRACKING_URI=http://10.194.9.119:5050`
