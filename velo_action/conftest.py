import os
from functools import lru_cache
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

import pytest
import yaml

from velo_action.settings import ActionInputs, GithubSettings

_ACTION_FILE = os.path.dirname(__file__) + "/../action.yml"


@pytest.fixture
def mock_generate_version_subprocess_run():
    with patch("velo_action.version.subprocess.run") as mock_subprocess_run:
        mock_subprocess_run.return_value = MagicMock(
            args=["git rev-parse --short HEAD"],
            returncode=0,
            stdout=b"1af9c7c\n",
            stderr=b"",
        )
        yield mock_subprocess_run


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
        workspace=".",
        sha="ffac537e6cbbf934b08745a378932722df287a53",
        ref_name="main",
        server_url="https://github.com",
        repository="octocat/Hello-World",
        actor="octocat",
        api_url="test",
        run_id="1",
        workflow="test",
    )


@pytest.fixture(scope="function")
def default_github_settings_env_vars(monkeypatch):
    monkeypatch.setenv("GITHUB_WORKSPACE", "test")
    monkeypatch.setenv("GITHUB_SHA", "ffac537e6cbbf934b08745a378932722df287a53")
    monkeypatch.setenv("GITHUB_REF_NAME", "test")
    monkeypatch.setenv("GITHUB_SERVER_URL", "test")
    monkeypatch.setenv("GITHUB_REPOSITORY", "test")
    monkeypatch.setenv("GITHUB_ACTOR", "test")
    monkeypatch.setenv("GITHUB_API_URL", "test")
    monkeypatch.setenv("GITHUB_RUN_ID", "test")
    monkeypatch.setenv("GITHUB_WORKFLOW", "test")


@pytest.fixture(scope="function")
def default_action_inputs_env_vars(monkeypatch):
    monkeypatch.setenv("INPUT_TOKEN", "test")
    monkeypatch.setenv("INPUT_PRECEDING_RUN_IDS", "test")
    monkeypatch.setenv("INPUT_TENANTS", "None")
    monkeypatch.setenv("INPUT_DEPLOY_TO_ENVIRONMENTS", "None")


@pytest.fixture
def default_action_inputs():
    with TemporaryDirectory() as tempdir:
        return ActionInputs(
            workspace=tempdir,
            token="test",
            preceding_run_ids="test",
        )


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
