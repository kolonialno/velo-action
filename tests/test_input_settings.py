# type: ignore
import os

import pytest
from pydantic import ValidationError

from velo_action.settings import Settings
from velo_action.test_utils import fill_default_envvars

# Test run in GitHub Action should behave as local
os.unsetenv("GITHUB_WORKSPACE")


def test_github_default_values(monkeypatch):
    fill_default_envvars(monkeypatch)
    sett = Settings()

    assert sett.create_release is False
    assert isinstance(sett.deploy_to_environments, list) and len(sett.tenants) == 0
    assert sett.log_level == "INFO"
    assert sett.octopus_api_key_secret == "velo_action_octopus_api_key"
    assert sett.octopus_server_secret == "velo_action_octopus_server"
    assert sett.project is None
    assert sett.service_account_key is None
    assert isinstance(sett.tenants, list) and len(sett.tenants) == 0
    assert sett.velo_artifact_bucket_secret == "velo_action_artifacts_bucket_name"
    assert sett.version is None
    assert sett.wait_for_deployment is False
    assert sett.workspace == os.getcwd()


def test_default_values():
    sett = Settings.parse_obj(
        {
            "workspace": os.getcwd(),  # Needs to be a valid dir
        }
    )
    assert sett.create_release is False
    assert isinstance(sett.deploy_to_environments, list) and len(sett.tenants) == 0
    assert sett.log_level == "INFO"
    assert sett.octopus_api_key_secret is None
    assert sett.octopus_server_secret is None
    assert sett.project is None
    assert sett.service_account_key is None
    assert isinstance(sett.tenants, list) and len(sett.tenants) == 0
    assert sett.velo_artifact_bucket_secret is None
    assert sett.version is None
    assert sett.wait_for_deployment is False
    assert sett.workspace == os.getcwd()


def test_parse_none():
    sett = Settings.parse_obj(
        {
            "deploy_to_environments": "None",
            "octopus_api_key_secret": "None",
            "octopus_server_secret": "None",
            "project": "None",
            "service_account_key": "None",
            "tenants": "None",
            "velo_artifact_bucket_secret": "None",
            "version": "None",
        }
    )

    assert sett.octopus_api_key_secret is None
    assert sett.octopus_server_secret is None
    assert sett.project is None
    assert sett.service_account_key is None
    assert sett.velo_artifact_bucket_secret is None
    assert sett.version is None


def test_parse_empty_list(monkeypatch):
    # pylint: disable=use-implicit-booleaness-not-comparison
    fill_default_envvars(monkeypatch)
    monkeypatch.setenv("INPUT_TENANTS", "")
    monkeypatch.setenv("INPUT_DEPLOY_TO_ENVIRONMENTS", "")
    sett = Settings()
    assert sett.tenants == []
    assert sett.deploy_to_environments == []


def test_parse_none_list(monkeypatch):
    # pylint: disable=use-implicit-booleaness-not-comparison
    fill_default_envvars(monkeypatch)
    monkeypatch.setenv("INPUT_TENANTS", "None")
    monkeypatch.setenv("INPUT_DEPLOY_TO_ENVIRONMENTS", "None")
    sett = Settings()
    assert sett.tenants == []
    assert sett.deploy_to_environments == []


def test_parse_1item_list(monkeypatch):
    fill_default_envvars(monkeypatch)
    monkeypatch.setenv("INPUT_TENANTS", "Some")
    monkeypatch.setenv("INPUT_DEPLOY_TO_ENVIRONMENTS", "Some")
    sett = Settings()
    assert sett.tenants == ["Some"]
    assert sett.deploy_to_environments == ["Some"]


def test_parse_2item_list(monkeypatch):
    fill_default_envvars(monkeypatch)
    monkeypatch.setenv("INPUT_TENANTS", "Some,More")
    monkeypatch.setenv("INPUT_DEPLOY_TO_ENVIRONMENTS", "Some,More")
    sett = Settings()
    assert sett.tenants == ["Some", "More"]
    assert sett.deploy_to_environments == ["Some", "More"]


def test_fail_on_unknown_log_level():
    with pytest.raises(ValidationError):
        Settings(log_level="INVALID_LOG_LEVEL")


def test_assume_fail_invalid_workspace(monkeypatch):
    fill_default_envvars(monkeypatch)
    monkeypatch.setenv("INPUT_WORKSPACE", "does_not_exist")
    with pytest.raises(ValidationError):
        Settings()
    monkeypatch.setenv("INPUT_WORKSPACE", "./poetry.lock")
    with pytest.raises(ValidationError):
        Settings()


def test_use_github_workspace_as_fallback(monkeypatch):
    fill_default_envvars(monkeypatch)
    monkeypatch.setenv("GITHUB_WORKSPACE", "/var")
    monkeypatch.delenv("INPUT_WORKSPACE")
    sett = Settings()
    assert sett.workspace == "/var"

    monkeypatch.setenv("INPUT_WORKSPACE", "/etc")
    sett = Settings()
    assert sett.workspace == "/etc"
