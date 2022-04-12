# pylint: disable=unused-argument
import pytest
from pydantic import ValidationError

from velo_action.settings import GithubSettings


def test_github_settings_from_env_vars_sucess(default_github_settings_env_vars):
    settings = GithubSettings()
    assert settings.workspace == "test"
    assert settings.sha == "ffac537e6cbbf934b08745a378932722df287a53"
    assert settings.ref_name == "test"
    assert settings.server_url == "test"
    assert settings.actor == "test"


def test_github_settings_wrong_sha(default_github_settings_env_vars, monkeypatch):
    monkeypatch.setenv("GITHUB_SHA", "test")
    with pytest.raises(ValidationError):
        GithubSettings()
