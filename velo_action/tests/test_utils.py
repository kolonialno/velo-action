from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import mock_open, patch

import pytest
from semantic_version import SimpleSpec, Version

from velo_action.utils import (
    find_matching_version,
    read_field_from_app_spec,
    read_velo_settings,
)


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
        read_velo_settings(Path("/tmp/not-found"))


def test_read_app_spec_file_sucess():
    """Read project and velo_version from app.yml"""
    with TemporaryDirectory() as tmpdir:
        filename = Path.joinpath(Path(tmpdir), "app.yml")
        with open(filename, "w", encoding="utf-8") as file:
            file.write("velo_version: 1.0.0\nproject: test\n")
            file.flush()
            velo_settings = read_velo_settings(Path(tmpdir))
            assert velo_settings.project == "test"
            assert velo_settings.version_spec == SimpleSpec("1.0.0")


@pytest.mark.parametrize(
    "app_spec",
    ['"project": "test"', 'velo_version: "1.0.2"'],
)
def test_read_app_spec_file_exit_on_missing_fields(app_spec):
    """SystemExit if one of the required fields are not present

    Here: project and velo_version
    """
    with TemporaryDirectory() as temp:
        filename = Path.joinpath(Path(temp), "app.yml")
        with open(filename, "w", encoding="utf-8") as file:
            file.write(app_spec)
            file.flush()
            with pytest.raises(SystemExit):
                read_velo_settings(Path(temp))


@pytest.mark.parametrize(
    "app_spec,field,result",
    [
        ("project: test", "project", "test"),
        ("dummy_field: some:test", "dummy_field", "some"),
        ('velo_version: ">=0.4,<0.5"', "velo_version", ">=0.4,<0.5"),
        ("velo_version: no_quotes", "velo_version", "no_quotes"),
        ("velo_version: ~=2.2", "velo_version", "~=2.2"),
    ],
)
def test_read_field_from_app_spec_sucess(app_spec, field, result):
    """Verify the read field from app spec handles edge cases."""

    with patch("builtins.open", mock_open(read_data=app_spec)):
        field = read_field_from_app_spec(field=field, filename=Path("/mocked"))
        assert field == result


def test_read_field_from_app_spec_failure():
    """Verify the read field from app spec handles edge cases."""

    with pytest.raises(ValueError):
        with patch("builtins.open", mock_open(read_data="project: test")):
            read_field_from_app_spec(field="not_present", filename=Path("/mocked"))
