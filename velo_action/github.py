import os
import logging

logger = logging.getLogger(name="github")


def actions_output(key, value):
    logger.info("Setting Github actions output: {key}={value}")
    os.system(f'echo "::set-output name={key}::{value}"')
