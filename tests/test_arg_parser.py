import pytest
from velo_action.action import parse_args


def test_assume_fail_arg_parser_noworkspace(monkeypatch):
    with pytest.raises(Exception):
        args = parse_args()


def test_assume_fail_arg_parser_errorworkspace(monkeypatch):
    monkeypatch.setenv("INPUT_WORKSPACE", "does_not_exist")
    with pytest.raises(Exception):
        args = parse_args()


def test_arg_parser_workspace(monkeypatch):
    monkeypatch.setenv("INPUT_WORKSPACE", ".")
    args = parse_args()
    assert True is True
    assert args.create_release is False
    assert args.deploy_to_environments == []
    assert args.log_level == "INFO"
    assert args.create_release is False


def test_arg_parser_github_workspace(monkeypatch):
    monkeypatch.setenv("GITHUB_WORKSPACE", ".")
    args = parse_args()
    assert True is True
    assert args.create_release is False
    assert args.deploy_to_environments == []
    assert args.log_level == "INFO"
    assert args.create_release is False


def test_arg_parser_workspace_project_create_release(monkeypatch):
    monkeypatch.setenv("INPUT_WORKSPACE", ".")
    monkeypatch.setenv("INPUT_PROJECT", "testproject")
    monkeypatch.setenv("INPUT_CREATE_RELEASE", "True")
    args = parse_args()
    assert True is True
    assert args.create_release is True
    assert args.deploy_to_environments == []


def test_arg_parser_workspace_project_deploy_and_wait(monkeypatch):
    monkeypatch.setenv("INPUT_WORKSPACE", ".")
    monkeypatch.setenv("INPUT_PROJECT", "testproject")
    monkeypatch.setenv("INPUT_CREATE_RELEASE", "True")
    monkeypatch.setenv("INPUT_DEPLOY_TO_ENVIRONMENTS", "staging")
    args = parse_args()
    assert True is True
    assert args.create_release is True
    assert args.deploy_to_environments == ["staging"]
    assert args.wait_for_deployment is True


def test_arg_parser_workspace_project_deploy_and_nowait(monkeypatch):
    monkeypatch.setenv("INPUT_WORKSPACE", ".")
    monkeypatch.setenv("INPUT_PROJECT", "testproject")
    monkeypatch.setenv("INPUT_CREATE_RELEASE", "True")
    monkeypatch.setenv("INPUT_DEPLOY_TO_ENVIRONMENTS", "staging")
    monkeypatch.setenv("INPUT_WAIT_FOR_DEPLOYMENT", "False")
    args = parse_args()
    assert True is True
    assert args.create_release is True
    assert args.deploy_to_environments == ["staging"]
    assert args.wait_for_deployment is False


def test_arg_parser_workspace_project_deploy_multi_env(monkeypatch):
    monkeypatch.setenv("INPUT_WORKSPACE", ".")
    monkeypatch.setenv("INPUT_PROJECT", "testproject")
    monkeypatch.setenv("INPUT_CREATE_RELEASE", "True")
    monkeypatch.setenv("INPUT_DEPLOY_TO_ENVIRONMENTS", "staging,prod")
    args = parse_args()
    assert True is True
    assert args.create_release is True
    assert args.deploy_to_environments == ["staging", "prod"]
