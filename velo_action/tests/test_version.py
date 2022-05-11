# pylint: disable=unused-argument
from velo_action.version import generate_version


def test_generate_version(mock_generate_version_subprocess_run):
    version = generate_version()
    assert len(version) >= 7
    assert len(version) <= 40
