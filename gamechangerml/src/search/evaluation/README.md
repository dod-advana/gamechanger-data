# Instructions for testing:

## Starting a local MLFlow server

- Open a terminal and run `mlflow server`
- The terminal should display a line indicating "Listening at: http://127.0.0.1:5000". If the address is different, take not of the address
- On another terminal, run `export MLFLOW_SERVER="http://127.0.0.1:5000"`. This is done locally but when our dedicated server is up and running, the address can be changed to log to our mlflow server.

## Downloading a dataset from our S3
- cd to `gamechanger`
- Run `. gamechangerml/setup_env.sh`
- Run `python gamechangerml/src/search/evaluation/dl_data_cli.py`. A list of available datasets to download should show up. The datasets are formatted "<dataset_name>/v<version_num>"
- Run `python gamechangerml/src/search/evaluation/dl_data_cli.py -d msmarco_100k -c <path/to/local/dataset/dir>`. By default, it will always download the latest dataset.
- After a few seconds, the dataset will be downloaded to your local directory.

## Evaluating and Logging to MLFlow
- cd to `gamechangerml/src/search/evaluation/`
- Under `sample_data`, you can find an answers.json and a params.json file for sample purposes.
- Run `python eval_cli.py -a sample_data/answers.json -c <path/to/local/dataset/dir> -p sample_data/params.json -e "sample_upload"`
- On a browser, go to the mlflow server address ("http://127.0.0.1:5000"). You should see be able to see the metrics you uploaded on the left.

## Frequently Asked Questions

### ModuleNotFoundError: No module named 'gamechangerml'

You would need to add the path to GameChanger under your PYTHONPATH. Here are ways to do it:

1. Run `EXPORT PYTHONPATH=$PYTHONPATH:<path/to/gamechanger/folder>`. This is a one time fix which needs to be ran every time you open a new terminal.
2. Add `PYTHONPATH=$PYTHONPATH:<path/to/gamechanger/folder>` to your `~/.bashrc` file is the recommended way.

# Generating the Gold Standard GAMECHANGER dataset

This tutorial will walk you through how to create and upload an evaluation dataset from the GAMECHANGER corpus.

1. Create a `.csv` file containing the headers `["query", "document"]`. Each row will be a pair of `query`, the search query, and the `document`, the document name.
2. Download the GAMECHANGER corpus into your local directory.
3. Run `python gamechangerml/src/search/evaluation/gen_gold_cli.py -q <path/to/query/csv/file> -c <path/to/corpus> -o <path/to/output/json/file>`\
4. If the document name doesn't match any of the documents in the corpus, the script returns the top 5 document names from the corpus that is closest to the query.
5. Construct the evaluation dataset by combining the documents and the relations file into a single folder.
6. Run `python` then run the following commands:
```
from gamechangerml.src.utilities.utils import store_eval_data

store_eval_data(<path/to/evaluation/folder>, <version number>)
```

We separated the function to store the evaluation data into the S3 bucket to give the user time to inspect the evaluation data.
