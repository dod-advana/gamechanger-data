#!/usr/bin/env bash

cat <<EOF

  STARTING CREATE CLONE RUN
  $(date "+DATE: %Y-%m-%d TIME: %H:%M:%S")

EOF

# main
python -m clone_creator run

cat <<EOF

  SUCCESSFULLY FINISHED CREATE CLONE RUN
  $(date "+DATE: %Y-%m-%d TIME: %H:%M:%S")

EOF