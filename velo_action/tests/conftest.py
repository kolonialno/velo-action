import os.path
from functools import lru_cache

import pytest
import yaml

from velo_action.settings import ActionInputs, GithubSettings

_ACTION_FILE = os.path.dirname(__file__) + "/../../action.yml"


def fill_default_action_envvars(monkeypatch):
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


@pytest.fixture
def default_github_settings():
    return GithubSettings(
        github_workspace=".",
        github_sha="ffac537e6cbbf934b08745a378932722df287a53",
        github_ref_name="main",
        github_server_url="https://github.com",
        github_repository="octocat/Hello-World",
    )


@pytest.fixture
def default_settings(default_github_settings):
    return ActionInputs(gh=default_github_settings)


@pytest.fixture(scope="session", autouse=True)
def unsett_dot_env_variables():
    """Unset the variables in .env file.
    These should not affect test.
    """
    os.unsetenv("INPUT_WORKSPACE")
    os.unsetenv("INPUT_VERSION")
    os.unsetenv("INPUT_LOG_LEVEL")

    os.unsetenv("INPUT_CREATE_RELEASE")
    os.unsetenv("INPUT_WAIT_FOR_SUCCESS_SECONDS")
    os.unsetenv("INPUT_PROJECT")

    os.unsetenv("GITHUB_WORKSPACE")
    os.unsetenv("GITHUB_SHA")
    os.unsetenv("GITHUB_REF_NAME")
