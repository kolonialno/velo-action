# pylint: disable=invalid-name
from velo_action.settings import GithubSettings


def create_release_notes(gh: GithubSettings) -> str:
    """Create release notes for a Octopus Deploy
    Shall be HTML formatted.
    """
    return f"""
<b>Commit</b>: <a href={gh.github_server_url}/{gh.github_repository}/commit/{gh.github_sha}>{gh.github_sha}</a>
<br>
<br>
<b>Branch name</b>: <a href={gh.github_server_url}/{gh.github_repository}/tree/{gh.github_ref_name}>{gh.github_ref_name}</a>
<br>
<br>
<b>Created by </b>: <a href={gh.github_server_url}/{gh.github_actor}>{gh.github_actor}</a>
""".replace(
        "\n", " "
    )
