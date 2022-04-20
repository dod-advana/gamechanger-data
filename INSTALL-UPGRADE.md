<img src="./img/tags/GAMECHANGER-NoPentagon_RGB@3x.png" align="right"
     alt="Mission Vision Icons" width="300" >

<h1>
<img src="./img/icons/RPA.png" alt="Data Engineering" width="70" aling="left"  >
     Data Engineering
</h1> 

`gamechanger-data` focuses on the data engineering work of gamechanger. To see all repositories [gamechanger](https://github.com/dod-advana/gamechanger)


## How to Setup Local Env for Development

This section uses `pyenv` as a python version manager, [poetry](https://python-poetry.org/docs/) as a python package manager, and uses Python version 3.8.13.

### MacOS / Linux

> **Note:**
> - You can use [pyenv](https://github.com/pyenv/pyenv) to handle various python versions on your machine
> - This project [poetry](https://python-poetry.org/docs/) as it's package manager
> - The python version for this project is `3.8.13`
> - If you don't want to use `poetry` as your package manager, a new requirements file has been added [here](./dev_tools/requirements/py38-requirements.txt) with the `python 3.8.13` dependencies

Follow the below instructions in order:

- (MacOS Only) Install `brew` then use it to install `tesseract`: `brew install tesseract-lang `
- For installing `pyenv`, follow the instructions in the README [here](https://github.com/pyenv/pyenv)
- Install `python`: `pyenv install 3.8.13`. To check if the installation was successful, run: `python -V` which should return 3.8.13
- Install `poetry`, follow the following instructions:

    ```bash
    curl -sSL https://install.python-poetry.org > get-poetry.py
    python get-poetry.py
    export PATH="$HOME/.local/bin:$PATH"
    poetry config virtualenvs.in-project true
    ```

- Install project's dependencies by running `poetry install`
- Activate the virtual environment by running: `poetry shell`

> **Note:** This project was originally set up for using `python 3.6`. With the `3.8.13` upgrade, there were some changes to the package depencency versions. You can see the list of changes here (**TODO: UPDATE LIST**).

## Run Tests
This project uses `pytest` as it's testing framework. See the [examples](https://docs.pytest.org/en/stable/example/index.html) or [documentation](https://docs.pytest.org/en/stable/index.html) page for more info. To make sure changes you've made to the code don't break functionality, update and run the test suite before pushing to github.

```bash
pytest tests/
```

## License & Contributions
See LICENSE.md (including licensing intent - INTENT.md) and CONTRIBUTING.md