#!/bin/bash
set -e
export GOOGLE_APPLICATION_CREDENTIALS='/key.json'

poetry run python velo_action/action.py
