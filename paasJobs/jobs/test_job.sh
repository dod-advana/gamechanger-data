#!/usr/bin/env bash

echo "TEST JOB IS RUNNING!!!!!"
sleep 5
echo "IT IS DONE!"

exit "${OVERRIDE_EXIT_CODE:-0}"