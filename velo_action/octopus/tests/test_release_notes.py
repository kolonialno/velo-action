from velo_action.octopus.release import create_release_notes
from velo_action.settings import GithubSettings


# @pytest.mark.skip("Only for local testing. Used to write release notes to HTML file")
def test_create_release_note_write_to_file() -> None:
    """Test use lokally to output the releas notes to a HTML file"""
    github = GithubSettings(
        workspace=".",
        sha="3b6bde232e73ee520d0fc3d38f836480ebde181a",
        ref_name="main",
        server_url="https://github.com",
        repository="kolonialno/example-deploy-project",
        actor="kolonialno",
    )
    notes = create_release_notes(github=github)

    with open("releasenotes.html", "w", encoding="utf-8") as file:
        file.write(notes)
