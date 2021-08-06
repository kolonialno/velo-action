import pytest
from velo_action.settings import Settings
from pydantic import ValidationError


def test_assume_fail_arg_parser_noworkspace(monkeypatch):
    with pytest.raises(ValidationError):
        s = Settings()


def test_assume_fail_arg_parser_errorworkspace(monkeypatch):
    monkeypatch.setenv("INPUT_WORKSPACE", "does_not_exist")
    with pytest.raises(ValidationError):
        s = Settings()


def test_arg_parser_workspace(monkeypatch):
    monkeypatch.setenv("INPUT_WORKSPACE", ".")
    s = Settings()
    assert s.create_release is False
    assert s.deploy_to_environments == []
    assert s.log_level == "INFO"
    assert s.create_release is False


def test_arg_parser_github_workspace(monkeypatch):
    monkeypatch.setenv("GITHUB_WORKSPACE", ".")
    s = Settings()
    assert s.create_release is False
    assert s.deploy_to_environments == []
    assert s.log_level == "INFO"
    assert s.create_release is False


def test_arg_parser_workspace_project_create_release(monkeypatch):
    monkeypatch.setenv("INPUT_WORKSPACE", ".")
    monkeypatch.setenv("INPUT_PROJECT", "testproject")
    monkeypatch.setenv("INPUT_CREATE_RELEASE", "True")
    s = Settings()
    assert s.create_release is True
    assert s.deploy_to_environments == []


def test_arg_parser_workspace_project_deploy_and_wait(monkeypatch):
    monkeypatch.setenv("INPUT_WORKSPACE", ".")
    monkeypatch.setenv("INPUT_PROJECT", "testproject")
    monkeypatch.setenv("INPUT_CREATE_RELEASE", "True")
    monkeypatch.setenv("INPUT_DEPLOY_TO_ENVIRONMENTS", "staging")
    s = Settings()
    assert s.create_release is True
    assert s.deploy_to_environments == ["staging"]
    assert s.wait_for_deployment is True


def test_arg_parser_workspace_project_deploy_and_nowait(monkeypatch):
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
    monkeypatch.setenv("INPUT_WORKSPACE", ".")
    monkeypatch.setenv("INPUT_PROJECT", "testproject")
    monkeypatch.setenv("INPUT_CREATE_RELEASE", "True")
    monkeypatch.setenv("INPUT_DEPLOY_TO_ENVIRONMENTS", "staging,prod")
    s = Settings()
    assert s.create_release is True
    assert s.deploy_to_environments == ["staging", "prod"]


def test_arg_parser_none_values(monkeypatch):
    monkeypatch.setenv("INPUT_WORKSPACE", ".")
    monkeypatch.setenv("INPUT_VERSION", "None")
    monkeypatch.setenv("INPUT_PROJECT", "None")
    monkeypatch.setenv("INPUT_TENANTS", "None")
    s = Settings()
    assert s.version is None
    assert s.project is None
    assert s.project is None
