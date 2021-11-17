#!/bin/bash
unset BASH_ENV PROMPT_COMMAND ENV
source /opt/app-root/bin/activate
exec "$@"