#!/usr/bin/env bash

cat <<EOF

  STARTING CREATE CLONE RUN
  $(date "+DATE: %Y-%m-%d TIME: %H:%M:%S")

EOF

# main
export SEND_NOTIFICATIONS="yes"
python -m gc_clone_maker run

cat <<EOF

  SUCCESSFULLY FINISHED CREATE CLONE RUN
  $(date "+DATE: %Y-%m-%d TIME: %H:%M:%S")

EOF