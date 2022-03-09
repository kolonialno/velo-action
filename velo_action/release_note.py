# pylint: disable=invalid-name
from velo_action.settings import GithubSettings


def create_release_notes(gh: GithubSettings) -> str:
    """Create release notes for a Octopus Deploy
    Shall be HTML formatted.
    """
    return f"""
<b>Commit</b>: <a href={gh.server_url}/{gh.repository}/commit/{gh.sha}>{gh.sha}</a>
<br>
<br>
<b>Branch name</b>: <a href={gh.server_url}/{gh.repository}/tree/{gh.ref_name}>{gh.ref_name}</a>
<br>
<br>
<b>Created by </b>: <a href={gh.server_url}/{gh.actor}>{gh.actor}</a>
""".replace(
        "\n", " "
    )
