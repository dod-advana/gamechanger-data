# GC Env Tests

Tool for validating env dependencies before they become deployment issues.

## Dev Guide
- This package should stand on its' own and never reference any other part of GC repo. - So that it can be shared with deployment engineers without bundling the rest of the code.

## How to Use
- Clone repo to separate (temporary) directory, e.g. `git clone https://github.com/dod-advana/gamechanger-data.git /tmp/gcdeptest`
- Activate the relevant python venv; e.g. `source /opt/gc-venv-current/bin/activate`
- Run test suite; e.g. `python -m unittest discover -v -b -s /tmp/gcdeptest/tests/dependency_checks" -p '*tests.py'`