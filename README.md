<img src="./img/tags/GAMECHANGER-NoPentagon_RGB@3x.png" align="right"
     alt="Mission Vision Icons" width="300" >
# Introduction

Over 15 thousand documents govern how the Department of Defense (DoD) operates. The documents exist in different repositories, often exist on different networks, are discoverable to different communities, are updated independently, and evolve rapidly. No single ability has ever existed that would enable navigation of the vast universe of governing requirements and guidance documents, leaving the Department unable to make evidence-based, data-driven decisions. Today GAMECHANGER offers a scalable solution with an authoritative corpus comprising a single trusted repository of all statutory and policy driven requirements based on Artificial-Intelligence (AI) enabled technologies.

#
<img src="./img/original/Brand_Platform.png" align="right"
     alt="Mission Vision Icons" width="320" >

### Vision

Fundamentally changing the way in which the DoD navigates its universe of requirements and makes decisions

### Mission
GAMECHANGER aspires to be the Department’s trusted solution for evidence-based, data-driven decision-making across the universe of DoD requirements by:

- Building the DoD’s authoritative corpus of requirements and policy to drive search, discovery, understanding, and analytic capabilities
- Operationalizing cutting-edge technologies, algorithms, models and interfaces to automate and scale the solution
- Fusing best practices from industry, academia, and government to advance innovation and research
- Engaging the open-source community to build generalizable and replicable technology

## License & Contributions
See LICENSE.md (including licensing intent - INTENT.md) and CONTRIBUTING.md

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
