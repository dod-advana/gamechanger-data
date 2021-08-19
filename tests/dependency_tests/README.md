# GC Env Tests

Tool for validating env dependencies before they become deployment issues.

## Dev Guide
- The test suites here should stand on their own, because intent is to vet dependencies that may or may not be in place. - So that it can be shared with deployment engineers without bundling the rest of the code.

## How to Use
- Clone repo to separate (temporary) directory, e.g. `git clone https://github.com/dod-advana/gamechanger-data.git /tmp/gcdeptest`
- Activate the relevant python venv; e.g. `source /opt/gc-venv-current/bin/activate`
- Run test suite; e.g. `GPU_PRESENT=no python -m unittest discover -v -b -s "/tmp/gcdeptest/tests/dependency_tests" -p 'test_*.py'`
    - If there is a GPU on the box that's supposed to be used by the env, change to `GPU_PRESENT=yes` in example above.
    - Note: `pytest` can also be used to run these tests, but it should not be required.
