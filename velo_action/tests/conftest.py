import os.path
from functools import lru_cache

import yaml

_ACTION_FILE = os.path.dirname(__file__) + "/../action.yml"


def fill_default_envvars(monkeypatch):
    """
    set all input envvars according to the GitHub action defaults
    """
    defaults = read_github_action_inputs_defaults()
    for var, default in defaults.items():
        monkeypatch.setenv("INPUT_" + var.upper(), default)


@lru_cache
def read_github_action_inputs_defaults() -> dict:
    """
    Get dict of defaults from action.yml
    """
    with open(_ACTION_FILE, mode="r", encoding="utf8") as file:
        data = yaml.safe_load(file)
        inputs = data.get("inputs", {})
        return {k: v.get("default") for k, v in inputs.items()}
