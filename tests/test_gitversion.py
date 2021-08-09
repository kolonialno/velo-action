import pytest
from pathlib import Path
from velo_action import gitversion


@pytest.mark.docker
def test_gitversion_version():
    """Verify correct gitversion.

    Must only run in velo-action container where gitversion is installed.
    """
    path = Path(__file__).resolve().parent.parent

    gv = gitversion.Gitversion(path)

    assert gv._gitversion_cli_exists()
    assert gv._version() == "1.0.0"
