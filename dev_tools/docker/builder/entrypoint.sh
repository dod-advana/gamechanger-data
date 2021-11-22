#!/bin/bash
unset BASH_ENV PROMPT_COMMAND ENV
source scl_source enable "rh-python${SCL_PYTHON_VERSION}" devtoolset-10
exec "$@"