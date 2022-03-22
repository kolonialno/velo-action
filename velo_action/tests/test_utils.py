from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from semantic_version import SimpleSpec, Version

from velo_action.utils import find_matching_version, read_app_spec


def test_should_find_version_that_is_exact_match():
    versions = ["1.0.0", "1.0.1", "1.0.2"]
    version_to_match = SimpleSpec("1.0.0")
    assert find_matching_version(versions, version_to_match) == Version("1.0.0")


def test_should_find_version_that_matches_major():
    versions = ["1.0.0", "1.0.1", "1.0.2"]
    version_to_match = SimpleSpec("1.*.*")
    assert find_matching_version(versions, version_to_match) == Version("1.0.2")


def test_should_find_version_that_matches_major_no_patch():
    versions = ["1.0.0", "1.0.1", "1.0.2"]
    version_to_match = SimpleSpec("1.*")
    assert find_matching_version(versions, version_to_match) == Version("1.0.2")


def test_should_find_version_that_matches_only_major():
    versions = ["1.0.0", "1.0.1", "1.0.2"]
    version_to_match = SimpleSpec("1")
    assert find_matching_version(versions, version_to_match) == Version("1.0.2")


def test_should_find_version_that_matches_only_major_highest_minor():
    versions = ["1.7.0", "1.0.1", "1.0.2"]
    version_to_match = SimpleSpec("1")
    assert find_matching_version(versions, version_to_match) == Version("1.7.0")


def test_should_find_version_that_matches_only_major_highest_minor_low():
    versions = ["0.2.0", "0.2.10", "1.0.2"]
    version_to_match = SimpleSpec("0.2")
    assert find_matching_version(versions, version_to_match) == Version("0.2.10")


def test_read_app_spec_file_not_found():
    with pytest.raises(FileNotFoundError):
        read_app_spec(Path("/tmp/not-found"))


def test_read_app_spec_file_sucess():
    """Read project and velo_verison from app.yml"""
    with TemporaryDirectory() as tmpdir:
        filename = Path.joinpath(Path(tmpdir), "app.yml")
        with open(filename, "w", encoding="utf-8") as file:
            file.write("velo_version: 1.0.0\nproject: test\n")
            file.flush()
            velo_settings = read_app_spec(Path(tmpdir))
            assert velo_settings.project == "test"
            assert velo_settings.version_spec == SimpleSpec("1.0.0")


@pytest.mark.parametrize("app_spec", ["project: test", "velo_version: 1.0.2"])
def test_read_app_spec_file_exit_on_missing_fields(app_spec):
    """Exit if the project attribute is not present"""
    with TemporaryDirectory() as temp:
        filename = Path.joinpath(Path(temp), "app.yml")
        with open(filename, "w", encoding="utf-8") as file:
            file.write(app_spec)
            file.flush()
            with pytest.raises(SystemExit):
                read_app_spec(Path(temp))
