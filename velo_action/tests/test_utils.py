import pytest

from velo_action.utils import find_matching_version, read_app_spec


def test_should_find_version_that_is_exact_match():
    versions = ["1.0.0", "1.0.1", "1.0.2"]
    version_to_match = "1.0.0"
    assert find_matching_version(versions, version_to_match) == "1.0.0"


def test_should_find_version_that_matches_major():
    versions = ["1.0.0", "1.0.1", "1.0.2"]
    version_to_match = "1.*.*"
    assert find_matching_version(versions, version_to_match) == "1.0.2"


def test_should_find_version_that_matches_major_no_patch():
    versions = ["1.0.0", "1.0.1", "1.0.2"]
    version_to_match = "1.*"
    assert find_matching_version(versions, version_to_match) == "1.0.2"


def test_should_find_version_that_matches_only_major():
    versions = ["1.0.0", "1.0.1", "1.0.2"]
    version_to_match = "1"
    assert find_matching_version(versions, version_to_match) == "1.0.2"


def test_should_find_version_that_matches_only_major_highest_minor():
    versions = ["1.7.0", "1.0.1", "1.0.2"]
    version_to_match = "1"
    assert find_matching_version(versions, version_to_match) == "1.7.0"


def test_should_find_version_that_matches_only_major_highest_minor_low():
    versions = ["0.2.0", "0.2.10", "1.0.2"]
    version_to_match = "0.2"
    assert find_matching_version(versions, version_to_match) == "0.2.10"


def test_read_app_spec_file_not_found():
    with pytest.raises(FileNotFoundError):
        read_app_spec("/tmp/not-found")
