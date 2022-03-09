# pylint: disable=unused-argument
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from velo_action.settings import ActionInputs, resolve_workspace
from velo_action.tests.conftest import fill_default_action_envvars


@patch("velo_action.settings.generate_version", return_value="4be1d57")
def test_github_default_values(generate_version, monkeypatch):
    fill_default_action_envvars(monkeypatch)
    sett = ActionInputs()

    assert sett.create_release is False
    assert isinstance(sett.deploy_to_environments, list) and len(sett.tenants) == 0
    assert sett.log_level == "INFO"
    assert sett.octopus_api_key_secret == "velo_action_octopus_api_key"
    assert sett.octopus_server_secret == "velo_action_octopus_server"
    assert sett.service_account_key is None
    assert isinstance(sett.tenants, list) and len(sett.tenants) == 0
    assert sett.velo_artifact_bucket_secret == "velo_action_artifacts_bucket_name"
    assert sett.version == generate_version.return_value
    assert sett.wait_for_deployment is False
    assert sett.workspace is None


def test_input_action_use_provided_workspace():
    sett = ActionInputs.parse_obj(
        {
            "workspace": os.getcwd(),  # Needs to be a valid dir
        }
    )
    assert sett.workspace == os.getcwd()


def test_input_action_workspace_not_valid_path():
    """If the provided workspace path does not exist,
    throw error.
    """
    with pytest.raises(ValueError):
        ActionInputs.parse_obj({"workspace": "invalid_path"})


@patch("velo_action.settings.generate_version", return_value="4be1d57")
def test_parse_none(generate_version):
    """The Github Action only provides inputs as env vars.
    A None type will be parsed as 'None' string.
    We need to support this
    """
    sett = ActionInputs.parse_obj(
        {
            "deploy_to_environments": "None",
            "octopus_api_key_secret": "None",
            "octopus_server_secret": "None",
            "service_account_key": "None",
            "tenants": "None",
            "velo_artifact_bucket_secret": "None",
            "version": "None",
        }
    )
    assert sett.octopus_api_key_secret is None
    assert sett.octopus_server_secret is None
    assert sett.service_account_key is None
    assert sett.velo_artifact_bucket_secret is None
    assert sett.version is generate_version.return_value


def test_parse_empty_list(monkeypatch):
    # pylint: disable=use-implicit-booleaness-not-comparison
    fill_default_action_envvars(monkeypatch)
    monkeypatch.setenv("INPUT_TENANTS", "")
    monkeypatch.setenv("INPUT_DEPLOY_TO_ENVIRONMENTS", "")
    sett = ActionInputs()
    assert sett.tenants == []
    assert sett.deploy_to_environments == []


def test_parse_none_list(monkeypatch):
    # pylint: disable=use-implicit-booleaness-not-comparison
    fill_default_action_envvars(monkeypatch)
    monkeypatch.setenv("INPUT_TENANTS", "None")
    monkeypatch.setenv("INPUT_DEPLOY_TO_ENVIRONMENTS", "None")
    sett = ActionInputs()
    assert sett.tenants == []
    assert sett.deploy_to_environments == []


def test_parse_1item_list(monkeypatch):
    fill_default_action_envvars(monkeypatch)
    monkeypatch.setenv("INPUT_TENANTS", "Some")
    monkeypatch.setenv("INPUT_DEPLOY_TO_ENVIRONMENTS", "Some")
    sett = ActionInputs()
    assert sett.tenants == ["Some"]
    assert sett.deploy_to_environments == ["Some"]


def test_parse_2item_list(monkeypatch):
    fill_default_action_envvars(monkeypatch)
    monkeypatch.setenv("INPUT_TENANTS", "Some,More")
    monkeypatch.setenv("INPUT_DEPLOY_TO_ENVIRONMENTS", "Some,More")
    sett = ActionInputs()
    assert sett.tenants == ["Some", "More"]
    assert sett.deploy_to_environments == ["Some", "More"]


def test_fail_on_unknown_log_level():
    with pytest.raises(ValidationError):
        ActionInputs(log_level="INVALID_LOG_LEVEL")


def test_assume_fail_invalid_workspace(monkeypatch):
    fill_default_action_envvars(monkeypatch)
    monkeypatch.setenv("INPUT_WORKSPACE", "does_not_exist")
    with pytest.raises(ValidationError):
        ActionInputs()
    monkeypatch.setenv("INPUT_WORKSPACE", "./poetry.lock")
    with pytest.raises(ValidationError):
        ActionInputs()


def test_use_github_workspace_as_fallback(
    unsett_dot_env_variables, monkeypatch, default_github_settings
):
    fill_default_action_envvars(monkeypatch)
    with TemporaryDirectory() as tmpdir:
        path = str(Path(tmpdir).expanduser().resolve())

        default_github_settings.workspace = path
        monkeypatch.delenv("INPUT_WORKSPACE")

        sett = ActionInputs()

        sett.workspace = resolve_workspace(sett, default_github_settings)
        assert sett.workspace == path

        monkeypatch.setenv("INPUT_WORKSPACE", path)
        sett = ActionInputs()
        assert sett.workspace == path


def test_wait_for_deployment_becomes_wait_for_success_seconds(
    monkeypatch, unsett_dot_env_variables
):

    default = ActionInputs()
    assert default.wait_for_deployment is False
    assert default.wait_for_success_seconds == 0

    deprecated = ActionInputs(wait_for_deployment="True")
    assert deprecated.wait_for_deployment is False
    assert deprecated.wait_for_success_seconds == 600

    new = ActionInputs(wait_for_success_seconds="120")
    assert new.wait_for_deployment is False
    assert new.wait_for_success_seconds == 120

    both = ActionInputs(
        wait_for_deployment="True",
        wait_for_success_seconds="120",
    )
    assert both.wait_for_deployment is False
    assert both.wait_for_success_seconds == 120
