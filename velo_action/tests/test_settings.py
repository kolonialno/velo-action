import os
from unittest.mock import patch

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


@patch.dict(
    os.environ,
    {
        "GITHUB_WORKSPACE": "test",
        "GITHUB_SHA": "ffac537e6cbbf934b08745a378932722df287a53",
        "GITHUB_REF_NAME": "test",
        "GITHUB_SERVER_URL": "test",
        "GITHUB_REPOSITORY": "test",
        "GITHUB_ACTOR": "test",
    },
    clear=True,
)
def test_github_settings_from_env_vars_sucess():
    settings = GithubSettings()
    assert settings.workspace == "test"
    assert settings.sha == "ffac537e6cbbf934b08745a378932722df287a53"
    assert settings.ref_name == "test"
    assert settings.server_url == "test"
    assert settings.actor == "test"


@patch.dict(
    os.environ,
    {
        "GITHUB_WORKSPACE": "test",
        "GITHUB_SHA": "wrong",
        "GITHUB_REF_NAME": "test",
        "GITHUB_SERVER_URL": "test",
        "GITHUB_REPOSITORY": "test",
        "GITHUB_ACTOR": "test",
    },
    clear=True,
)
def test_github_settings_wrong_sha():
    with pytest.raises(ValidationError):
        GithubSettings()
