# pylint: disable=unused-argument
from unittest.mock import patch

import pytest

from velo_action.release_note import create_release_notes
from velo_action.settings import GithubSettings


@pytest.mark.skip("To view the output and check formatting. Uncomment to run")
@patch("velo_action.settings.generate_version", return_value="4be1d57")
def test_create_release_note_write_to_markdown(generate_version) -> None:

    settings = GithubSettings(
        workspace=".",
        sha="3b6bde232e73ee520d0fc3d38f836480ebde181a",
        ref_name="main",
        server_url="https://github.com",
        repository="kolonialno/example-deploy-project",
        actor="kolonialno",
    )

    notes = create_release_notes(settings)

    with open("releasenotes.html", "w", encoding="utf-8") as file:
        file.write(notes)
