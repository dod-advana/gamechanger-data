# GC Env Tests

Tool for validating env dependencies before they become deployment issues.

## Dev Guide
- This package should stand on its' own and never reference any other part of GC repo. - So that it can be shared with deployment engineers without bundling the rest of the code.

## Pre-Deployment Use
- zip up the tests module and share it with deployment engineers: `zip -x "**/__pycache__/*" -r tests.zip tests/`
- run tests, e.g. copy-paste <test-utils.sh> and then run `run_tests /opt/gc-transformer-venv-green ./tests.zip cpu_ml_api_prereqs`
    - alternately, unzip the `tests.zip` somewhere, activate the python venv that's supposed to be tested, and run all tests in relevant module within the unzipped dir like `python -m unittest discover -v -b -s "<test_module_location>" -p '*tests.py'`