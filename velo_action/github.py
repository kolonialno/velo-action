import os
import logging

logger = logging.getLogger(name="github")


def actions_output(key, value):
    logger.info("Github actions output:")
    os.system(f'echo "::set-output name={key}::{value}"')
