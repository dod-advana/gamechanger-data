#!/bin/bash
unset BASH_ENV PROMPT_COMMAND ENV
source scl_source enable rh-python38 devtoolset-10
exec "$@"