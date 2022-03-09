from unittest.mock import patch

import pytest

from velo_action.release_note import create_release_notes
from velo_action.settings import GithubSettings


@pytest.mark.skip("To view the output and check formatting. Uncomment to run")
@patch("velo_action.settings.generate_version", return_value="4be1d57")
def test_create_release_note_write_to_markdown(generate_version) -> None:

    gh = GithubSettings(
        github_workspace=".",
        github_sha="3b6bde232e73ee520d0fc3d38f836480ebde181a",
        github_ref_name="main",
        github_server_url="https://github.com",
        github_repository="kolonialno/example-deploy-project",
        github_actor="kolonialno",
    )

    notes = create_release_notes(gh)

    with open("releasenotes.html", "w") as f:
        f.write(notes)
