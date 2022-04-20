# pylint: disable=unused-argument
import pytest
from pydantic import ValidationError
from semantic_version import SimpleSpec

from velo_action.settings import GithubSettings, VeloSettings


@pytest.mark.parametrize("version_spec", ["1.2.3", ">5.2.1", ">=0.4,<0.5"])
def test_velo_settings_parse_version_valid(version_spec):

    settings = VeloSettings(
        project="ProjectName",
        velo_version=SimpleSpec(version_spec),
    )
    assert settings.version_spec == SimpleSpec(version_spec)


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
