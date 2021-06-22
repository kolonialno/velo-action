#!/bin/bash
set -e

# echo $INPUT_SERVICE_ACCOUNT_KEY | base64 -d > /key.json && cat key.json
# export GOOGLE_APPLICATION_CREDENTIALS="/key.json"

ls -la
pwd
which python

poetry run python velo_action/action.py
