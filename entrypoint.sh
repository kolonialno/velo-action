#!/bin/bash
set -e
export GOOGLE_APPLICATION_CREDENTIALS='/key.json'

ls -la
pwd
which python

poetry run python velo_action/action.py
