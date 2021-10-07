#!/usr/bin/env bash

cat <<EOF

  STARTING CHECK CRAWLER STATUS RUN
  $(date "+DATE: %Y-%m-%d TIME: %H:%M:%S")

EOF

# main
export SEND_NOTIFICATIONS="yes"
python -m gc_crawler_status_monitor run

cat <<EOF

  SUCCESSFULLY FINISHED CHECK CRAWLER STATUS RUN
  $(date "+DATE: %Y-%m-%d TIME: %H:%M:%S")

EOF