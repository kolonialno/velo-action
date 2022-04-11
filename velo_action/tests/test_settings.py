import os
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from velo_action.settings import GithubSettings


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
