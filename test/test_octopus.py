import pytest
import os
from velo_action import octopus


@pytest.mark.docker
def test_release_notes():

    octo = octopus.Octopus()
    release_notes = octo._release_notes()

    assert "commit_id" in release_notes
    assert "branch_name" in release_notes


@pytest.mark.docker
def test_octo_cli_version():
    """Verify correct octo cli version.

    Must only run in velo-action container where octo is installed.
    """
    octo = octopus.Octopus()

    assert octo._octo_cli_exists()
    assert octo._version() == "7.4.3256"
