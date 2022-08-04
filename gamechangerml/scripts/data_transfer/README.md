# gamechangerml/scripts/data_transfer

This directory contains scripts to upload/ download data to/ from S3.


## Overview

```
- gamechangerml/scripts/data_transfer
    |--download_eval_data.py        Download evaluation data
    |--download_corpus.py           Download the corpus (using Python)
    |--download_corpus.sh           Download the corpus (using Bash)
```


## Prerequisites:
1. Create a virtual environment with the Python version specified in [setup.py](../../../setup.py). For venv help, see [here](../../../docs/VENV.md).
2. Activate the virtual environment.
3. Install `gamechangerml` (you must do this every time there are updates to this repo).
    a. `cd` to your local `gamechanger-ml` repository.
    b. Run `pip install .`

## Usage
Before running a Python script:
- Activate the virtual environment (see [prerequisites](#prerequisites)).
- `cd` into your local `gamechanger-ml` repository
- Refresh your token with AWSAML

### download_eval_data.py
```
python gamechangerml/scripts/data_transfer/download_eval.py
```
- You will be prompted to enter information about what dataset to download and where.

### download_corpus.py
```
python gamechangerml/scripts/data_transfer/download_corpus.py
```

### download_corpus.sh
```
bash gamechangerml/scripts/data_transfer/download_eval.sh
```


## Notes
- Another resource for data transfer operations is [gamechangerml/src/data_transfer](../../../gamechangerml/src/data_transfer/).
