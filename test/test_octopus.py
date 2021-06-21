import pytest

from velo_action import octopus


def test_releaseNotes():

    octo = octopus.Octopus()
    releaseNotes = octo._releaseNotes()

    assert "commit_id" in releaseNotes
    assert "branch_name" in releaseNotes


@pytest.mark.docker
def test_octo_cli_version():
    """Verify correct octo cli version.

    Must only run in velo-action container where octo is installed.
    """
    octo = octopus.Octopus()

    assert octo._octo_cli_exists()
    assert octo._version() == "7.4.3256"
