<img src="./img/tags/GAMECHANGER-NoPentagon_RGB@3x.png" align="right"
     alt="Mission Vision Icons" width="300" >

<h1>
<img src="./img/icons/RPA.png" alt="Data Engineering" width="70" aling="left"  >
     Data Engineering
</h1> 

`gamechanger-data` focuses on the data engineering work of gamechanger. To see all repositories [gamechanger](https://github.com/dod-advana/gamechanger)


## (Linux) Dev/Prod Deployment Instructions

- Clone fresh `gamechanger-data` repo
- Setup python3.6 venv with packages in requirements.txt.
  - Create python3.6 venv, e.g. `python3 -m venv /opt/gc-venv-20210613`
  - Before installing packages, update pip/wheel/setuptools, e.g. `<venv>/bin/pip install --upgrade pip setuptools wheel`
  - Install packages from `requirements.txt`, with no additional dependencies, e.g. `<venv>/bin/pip install --no-deps -r requirements.txt`
- Set up symlink `/opt/gc-venv-current` to the freshly created venv, e.g. `ln -s /opt/gc-venv-20210613 /opt/gc-venv-current`
- Pull in other dependencies and configure repo with `env SCRIPT_ENV=<prod|dev> <repo>/paasJobs/configure_repo.sh`
    - Config script will let you know if everything was configured correctly and if all backends can be reached.
    
## How to Setup Local Env for Development

### MacOS / Linux
- (Linux Only) Follow instruction appropriate to repo to install `ocrmypdf` and its dependencies: https://ocrmypdf.readthedocs.io/en/latest/installation.html#installing-on-linux
- (MacOS Only) Install "brew" then use it to install tesseract `brew install tesseract-lang `
- Install Miniconda or Anaconda (Miniconda is much smaller)
    - `https://docs.conda.io/en/latest/miniconda.html`
- Create gamechanger python3.6 environment, like so:
    - `conda create -n gc python=3.6`
- Clone the repo and change into that dir `git clone ...; cd gamechanger`
- Activate conda environment and install requirements:
    - :bangbang: <span style="color:red"> reeeealy important - make sure you change into repo directory</span>
    - `conda activate gc`
    - `pip install --upgrade pip setuptools wheel`
    - `pip install -e '.[dev]'`  (quoting around .[dev] is <span style="color:red">important</span>)
- That's it.

### Windows

- Setup Windows Subsystem for Linux (WSL) environment
    - `https://docs.microsoft.com/en-us/windows/wsl/install-win10`
- (In WSL)
    - Install ocrmypdf dependencies following ubuntu instructions here: https://ocrmypdf.readthedocs.io/en/latest/installation.html#installing-on-linux
    - Install Miniconda or Anaconda (Miniconda is much smaller)
        - `https://docs.conda.io/en/latest/miniconda.html`
    - Create gamechanger python3.6 environment, like so:
        - `conda create -n gc python=3.6`
    - Clone the repo and change into that dir `git clone ...; cd gamechanger-data`
    - Activate conda environment and install requirements:
        - :bangbang: <span style="color:red"> reeeealy important - make sure you change into repo directory</span>
        - `conda activate gc`
        - `pip install --upgrade pip setuptools wheel`
        - `pip install -e '.[dev]'` (quoting around .[dev] is <span style="color:red">important</span>)
    - That's it, just activate that conda env if you want to use it inside the terminal.
    
## IDE SETUP

### How to Setup PyCharm IDE

Note: If you're using containerized env, you'll need Pro version of PyCharm and separate set of instructions - [here](https://www.jetbrains.com/help/pycharm/using-docker-as-a-remote-interpreter.html)


- Create new project by opening directory where you cloned the repository. PyCharm will
tell you that it sees existing repo there, just accept that and proceed.
- With your gc conda environment all good to go, change your `"Preferences -> Project -> Python Interpreter"`
to the **EXISTING** `gc` conda env you created. https://www.jetbrains.com/help/pycharm/conda-support-creating-conda-virtual-environment.html
- Now, change your `"Preferences -> Build, Execution, Deployment -> Console -> Python Console interpreter"`
to your `gc` conda interpreter env that you added earlier.
- That's it, you will now have correct env in Terminal, Python Console, and elsewhere in the IDE.

### How to Setup Visual Studio Code IDE

Note: if you're using containerized env, you'll need setup like [this](https://code.visualstudio.com/learn/develop-cloud/containers)

- Open the cloned dir in new workspace and make sure to set your conda `gc` venv as the python venv
https://code.visualstudio.com/docs/python/environments
- That's it, when you start new integrated terminals, they'll activate the right environment and
the syntax highlighting/autocompletion is going to work as it's supposed to.

## Common Issues

**My venv is broken somehow!**
- Delete the old conda environment and create a new one,
follow steps above to reinstall it.

## License & Contributions
See LICENSE.md (including licensing intent - INTENT.md) and CONTRIBUTING.md