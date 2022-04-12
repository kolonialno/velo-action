# pylint: disable=protected-access
from unittest.mock import patch

import pytest
from semantic_version import SimpleSpec, Version

from velo_action.octopus.client import OctopusClient
from velo_action.octopus.release import (
    VELO_BOOTSTRAPPER_ACTION_NAME,
    VELO_BOOTSTRAPPER_PACKAGE_ID,
    Release,
)
from velo_action.octopus.tests.test_decorators import Request, mock_client_requests
from velo_action.settings import VELO_TRACE_ID_NAME


@pytest.fixture
@mock_client_requests(
    [
        Request("head", "api", response=True),
        Request("get", "api/projects/ProjectName", response={"Id": "project-1"}),
        Request(
            "get",
            "api/projects/project-1/releases/1.2.3",
            response={
                "Id": "release-1",
                "ProjectId": "project-1",
                "Version": "1.2.3",
                "Links": {
                    "ProjectVariableSnapshot": "api/variables/variableset-project-1-s-1"
                },
            },
        ),
    ]
)
def prepared_release():
    client = OctopusClient()
    rel = Release.from_project_and_version(
        project_name="ProjectName", version="1.2.3", client=client
    )
    return rel


@pytest.fixture
@mock_client_requests(
    [
        Request("head", "api", response=True),
    ]
)
def client():
    return OctopusClient()


@mock_client_requests(
    [
        Request(
            "get",
            "api/Spaces-1/feeds/feeds-builtin/packages/versions?"
            f"packageId={VELO_BOOTSTRAPPER_PACKAGE_ID}&take=1000&includePreRelease=false&includeReleaseNotes=false",
            response={"Items": [{"Version": "0.1.9"}, {"Version": "1.0.0"}]},
        ),
        Request("head", "api/projects/project-1/releases/1.2.3", response=False),
        Request("get", "api/projects/Project-1", response={"Id": "project-1"}),
        Request(
            "post",
            "api/releases",
            payload={
                "ProjectId": "project-1",
                "ReleaseNotes": "Notes",
                "SelectedPackages": [
                    {"ActionName": VELO_BOOTSTRAPPER_ACTION_NAME, "Version": "0.1.9"}
                ],
                "Version": "1.2.3",
            },
            response={
                "Id": "release-1",
                "ProjectId": "project-1",
                "Version": "1.2.3",
            },
        ),
    ]
)
def test_create_release_with_packages(client, default_github_settings):
    """Verify that a release use the lates verion of the velo-bootstrapper package, when
    'velo_version' is not specified.
    """
    rel = Release(client)
    with patch(
        "velo_action.octopus.release.create_release_notes", return_value="Notes"
    ):
        rel.create(
            project_name="Project-1",
            project_version="1.2.3",
            github_settings=default_github_settings,
            velo_version_spec=SimpleSpec("0.1.9"),
        )

    assert rel.id() == "release-1"
    assert rel.project_id() == "project-1"
    assert rel.version() == "1.2.3"


@mock_client_requests(
    [
        Request("get", "api/projects/Project-1", response={"Id": "project-1"}),
        Request("head", "api/projects/project-1/releases/1.2.3", response=False),
        Request(
            "post",
            "api/releases",
            payload={
                "ProjectId": "project-1",
                "ReleaseNotes": "Notes",
                "SelectedPackages": [
                    {"ActionName": VELO_BOOTSTRAPPER_ACTION_NAME, "Version": "1.1.1"}
                ],
                "Version": "1.2.3",
            },
            response={
                "Id": "release-1",
                "ProjectId": "project-1",
                "Version": "1.2.3",
            },
        ),
        Request(
            "get",
            (
                "api/Spaces-1/feeds/feeds-builtin/packages/versions?"
                f"packageId={VELO_BOOTSTRAPPER_PACKAGE_ID}&take=1000&includePreRelease=false&includeReleaseNotes=false"
            ),
            response={"Items": [{"Version": "0.1.9"}, {"Version": "1.1.1"}]},
        ),
    ]
)
def test_create_release_with_packages_specific_velo_version(
    client, default_github_settings
):
    """Create a release with a spesific Velo version that exists"""
    rel = Release(client)
    with patch(
        "velo_action.octopus.release.create_release_notes", return_value="Notes"
    ):
        rel.create(
            "Project-1",
            "1.2.3",
            github_settings=default_github_settings,
            velo_version_spec=SimpleSpec(">1.0.0"),
        )

    assert rel.id() == "release-1"
    assert rel.project_id() == "project-1"
    assert rel.version() == "1.2.3"


@mock_client_requests(
    [
        Request("get", "api/projects/ProjectName", response={"Id": "project-1"}),
        Request(
            "get",
            "api/projects/project-1/releases/1.2.3",
            response={"Id": "release-1", "ProjectId": "project-1", "Version": "1.2.3"},
        ),
    ]
)
def test_by_project_name_and_version(client):
    release = Release.from_project_and_version(
        project_name="ProjectName", version="1.2.3", client=client
    )

    assert release.id() == "release-1"
    assert release.project_id() == "project-1"
    assert release.version() == "1.2.3"


@mock_client_requests(
    [
        Request(
            "get",
            "api/variables/variableset-project-1-s-1",
            response={
                "Variables": [
                    {
                        "Id": "abcdef0123456789",
                        "Name": VELO_TRACE_ID_NAME,
                    }
                ]
            },
        ),
    ]
)
def test_form_variables(prepared_release):
    var_ids = prepared_release.form_variable_id_mapping()
    assert var_ids == {VELO_TRACE_ID_NAME: "abcdef0123456789"}


@mock_client_requests(
    [
        Request(
            "get",
            "api/projects/project-1/deploymentprocesses/template",
            response={
                "Packages": [
                    {
                        "FeedId": "feed-1",
                        "PackageId": "package-1",
                        "ActionName": "FirstAction",
                    }
                ]
            },
        ),
        Request(
            "get",
            r"api/feeds/feed-1/packages/versions?packageId=package-1&preReleaseTag=^(|\+.*)$&take=1",
            response={"Items": [{"Version": "0.1.9"}]},
        ),
    ]
)
def test_determine_latest_deploy_packages(prepared_release):
    assert prepared_release._determine_latest_deploy_packages(
        prepared_release.project_id()
    ) == [{"ActionName": "FirstAction", "Version": "0.1.9"}]


@mock_client_requests(
    [
        Request("get", "api/projects/ProjectName", response={"Id": "project-1"}),
        Request("head", "api/projects/project-1/releases/v1", response=False),
    ]
)
def test_exists_not(client):
    assert Release.exists("ProjectName", "v1", client=client) is False


@mock_client_requests(
    [
        Request("get", "api/projects/ProjectName", response={"Id": "project-1"}),
        Request("head", "api/projects/project-1/releases/v1", response=True),
    ]
)
def test_exists(client):
    assert Release.exists("ProjectName", "v1", client=client) is True


@mock_client_requests(
    [
        Request(
            "get",
            (
                "api/Spaces-1/feeds/feeds-builtin/packages/versions?"
                f"packageId={VELO_BOOTSTRAPPER_PACKAGE_ID}&take=1000&includePreRelease=false&includeReleaseNotes=false"
            ),
            response={"Items": [{"Version": "0.1.9"}, {"Version": "1.0.0"}]},
        ),
    ]
)
def test_list_available_deploy_packages(client):
    rel = Release(client)
    versions = rel.list_available_deploy_packages()
    assert versions == ["0.1.9", "1.0.0"]
    assert len(versions) == 2


@mock_client_requests(
    [
        Request(
            "get",
            "api/Spaces-1/feeds/feeds-builtin/packages/versions?"
            f"packageId={VELO_BOOTSTRAPPER_PACKAGE_ID}&take=1000&includePreRelease=false&includeReleaseNotes=false",
            response={"Items": [{"Version": "0.1.9"}, {"Version": "1.0.0"}]},
        ),
    ]
)
def test_resolve_velo_bootstrapper_version_no_velo_version(prepared_release):
    """When a velo_version does not exist. Exit with an error"""
    version = prepared_release._resolve_velo_bootstrapper_version(SimpleSpec("0.0.1"))
    assert version is None


@mock_client_requests(
    [
        Request(
            "get",
            "api/Spaces-1/feeds/feeds-builtin/packages/versions?"
            f"packageId={VELO_BOOTSTRAPPER_PACKAGE_ID}&take=1000&includePreRelease=false&includeReleaseNotes=false",
            response={"Items": [{"Version": "0.1.9"}, {"Version": "1.0.0"}]},
        ),
    ]
)
def test_resolve_velo_bootstrapper_version_exist(prepared_release):
    """When a velo_version exist, return it"""
    version = prepared_release._resolve_velo_bootstrapper_version(SimpleSpec("0.1.9"))
    assert version == Version("0.1.9")


def test_create_octopus_package_payload_with_velo_version(prepared_release):
    """When a velo_version is spesified, use that version"""
    assert prepared_release._create_octopus_package_payload(
        package=VELO_BOOTSTRAPPER_ACTION_NAME, version=Version("0.1.9")
    ) == [{"ActionName": VELO_BOOTSTRAPPER_ACTION_NAME, "Version": "0.1.9"}]
