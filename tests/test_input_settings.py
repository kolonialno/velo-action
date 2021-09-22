import pytest
from velo_action.settings import Settings
from velo_action.test_utils import fill_default_envvars
from pydantic import ValidationError
import os

HAS_GITHUB_WORKSPACE = True if os.getenv("GITHUB_WORKSPACE") else False


@pytest.mark.skipif(
    HAS_GITHUB_WORKSPACE, reason="GITHUB_WORKSPACE is set, skipping this"
)
def test_assume_fail_arg_parser_noworkspace(monkeypatch):
    fill_default_envvars(monkeypatch)
    """Will be skipped when running in GH Action, since GITHUB_WORKSPACE is likely set by the environment"""
    with pytest.raises(ValidationError):
        s = Settings()


def test_assume_fail_arg_parser_errorworkspace(monkeypatch):
    fill_default_envvars(monkeypatch)
    monkeypatch.setenv("INPUT_WORKSPACE", "does_not_exist")
    with pytest.raises(ValidationError):
        s = Settings()


def test_assume_fail_arg_parser_fallback_workspace(monkeypatch):
    fill_default_envvars(monkeypatch)
    monkeypatch.setenv("INPUT_WORKSPACE", "None")
    monkeypatch.setenv("GITHUB_WORKSPACE", ".")
    s = Settings()
    assert s.workspace == "."


def test_arg_parser_workspace(monkeypatch):
    fill_default_envvars(monkeypatch)
    monkeypatch.setenv("INPUT_WORKSPACE", ".")
    s = Settings()
    assert s.create_release is False
    assert s.deploy_to_environments == []
    assert s.log_level == "INFO"
    assert s.create_release is False


def test_arg_parser_github_workspace(monkeypatch):
    fill_default_envvars(monkeypatch)
    monkeypatch.setenv("GITHUB_WORKSPACE", ".")
    s = Settings()
    assert s.create_release is False
    assert s.deploy_to_environments == []
    assert s.log_level == "INFO"
    assert s.create_release is False


def test_arg_parser_workspace_project_create_release(monkeypatch):
    fill_default_envvars(monkeypatch)
    monkeypatch.setenv("INPUT_WORKSPACE", ".")
    monkeypatch.setenv("INPUT_PROJECT", "testproject")
    monkeypatch.setenv("INPUT_CREATE_RELEASE", "True")
    s = Settings()
    assert s.create_release is True
    assert s.deploy_to_environments == []


def test_arg_parser_workspace_project_none_environments(monkeypatch):
    fill_default_envvars(monkeypatch)
    monkeypatch.setenv("INPUT_WORKSPACE", ".")
    monkeypatch.setenv("INPUT_PROJECT", "testproject")
    monkeypatch.setenv("INPUT_DEPLOY_TO_ENVIRONMENTS", "None")
    s = Settings()
    assert s.create_release is False
    assert s.deploy_to_environments == []


def test_arg_parser_workspace_project_deploy_and_wait(monkeypatch):
    fill_default_envvars(monkeypatch)
    monkeypatch.setenv("INPUT_WORKSPACE", ".")
    monkeypatch.setenv("INPUT_PROJECT", "testproject")
    monkeypatch.setenv("INPUT_CREATE_RELEASE", "True")
    monkeypatch.setenv("INPUT_DEPLOY_TO_ENVIRONMENTS", "staging")
    s = Settings()
    assert s.create_release is True
    assert s.deploy_to_environments == ["staging"]
    assert s.wait_for_deployment is False


def test_arg_parser_workspace_project_deploy_and_nowait(monkeypatch):
    fill_default_envvars(monkeypatch)
    monkeypatch.setenv("INPUT_WORKSPACE", ".")
    monkeypatch.setenv("INPUT_PROJECT", "testproject")
    monkeypatch.setenv("INPUT_CREATE_RELEASE", "True")
    monkeypatch.setenv("INPUT_DEPLOY_TO_ENVIRONMENTS", "staging")
    monkeypatch.setenv("INPUT_WAIT_FOR_DEPLOYMENT", "False")
    s = Settings()
    assert s.create_release is True
    assert s.deploy_to_environments == ["staging"]
    assert s.wait_for_deployment is False


def test_arg_parser_workspace_project_deploy_multi_env(monkeypatch):
    fill_default_envvars(monkeypatch)
    monkeypatch.setenv("INPUT_WORKSPACE", ".")
    monkeypatch.setenv("INPUT_PROJECT", "testproject")
    monkeypatch.setenv("INPUT_CREATE_RELEASE", "True")
    monkeypatch.setenv("INPUT_DEPLOY_TO_ENVIRONMENTS", "staging,prod")
    s = Settings()
    assert s.create_release is True
    assert s.deploy_to_environments == ["staging", "prod"]


def test_arg_parser_none_values(monkeypatch):
    fill_default_envvars(monkeypatch)
    monkeypatch.setenv("INPUT_WORKSPACE", ".")
    monkeypatch.setenv("INPUT_VERSION", "None")
    monkeypatch.setenv("INPUT_PROJECT", "None")
    monkeypatch.setenv("INPUT_TENANTS", "None")
    s = Settings()
    assert s.version is None
    assert s.project is None
    assert s.project is None
