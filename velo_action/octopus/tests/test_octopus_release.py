import pytest

from velo_action.octopus.client import OctopusClient
from velo_action.octopus.release import Release
from velo_action.octopus.tests.test_decorators import Request, mock_client_requests
from velo_action.settings import VELO_TRACE_ID_NAME


@pytest.fixture
@mock_client_requests(
    [
        Request("head", "api", response=True),
        Request("get", "api/projects/ProjectName", response={"Id": "project-1"}),
        Request(
            "get",
            "api/projects/project-1/releases/v1.2.3",
            response={
                "Id": "release-1",
                "ProjectId": "project-1",
                "Version": "v1.2.3",
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
        project_name="ProjectName", version="v1.2.3", client=client
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
        Request("get", "api/projects/ProjectName", response={"Id": "project-1"}),
        Request("head", "api/projects/project-1/releases/v1.2.3", response=False),
        Request(
            "post",
            "api/releases",
            payload={
                "ProjectId": "project-1",
                "ReleaseNotes": '"Notes"',  # Json encoded
                "Version": "v1.2.3",
            },
            response={
                "Id": "release-1",
                "ProjectId": "project-1",
                "Version": "v1.2.3",
            },
        ),
    ]
)
def test_create_release_without_packages(client):
    rel = Release(client)
    rel.create("ProjectName", "v1.2.3", "Notes", auto_select_packages=False)

    assert rel.id() == "release-1"
    assert rel.project_id() == "project-1"
    assert rel.version() == "v1.2.3"


@mock_client_requests(
    [
        Request("get", "api/projects/Project-1", response={"Id": "project-1"}),
        Request("head", "api/projects/project-1/releases/v1.2.3", response=False),
        Request(
            "get",
            "api/projects/project-1/deploymentprocesses/template",
            response={
                "Packages": [
                    {
                        "FeedId": "feed-1",
                        "PackageId": "package-1",
                        "ActionName": "AnAction",
                    }
                ]
            },
        ),
        Request(
            "get",
            r"api/feeds/feed-1/packages/versions?packageId=package-1&preReleaseTag=^(|\+.*)$&take=1",
            response={"Items": [{"Version": "v0.1.9"}]},
        ),
        Request(
            "post",
            "api/releases",
            payload={
                "ProjectId": "project-1",
                "ReleaseNotes": '"Notes"',  # Json encoded
                "SelectedPackages": [{"ActionName": "AnAction", "Version": "v0.1.9"}],
                "Version": "v1.2.3",
            },
            response={
                "Id": "release-1",
                "ProjectId": "project-1",
                "Version": "v1.2.3",
            },
        ),
    ]
)
def test_create_release_with_packages(client):
    rel = Release(client)
    rel.create("Project-1", "v1.2.3", "Notes", auto_select_packages=True)

    assert rel.id() == "release-1"
    assert rel.project_id() == "project-1"
    assert rel.version() == "v1.2.3"


@mock_client_requests(
    [
        Request("get", "api/projects/ProjectName", response={"Id": "project-1"}),
        Request(
            "get",
            "api/projects/project-1/releases/v1.2.3",
            response={"Id": "release-1", "ProjectId": "project-1", "Version": "v1.2.3"},
        ),
    ]
)
def test_by_project_name_and_version(client):
    release = Release.from_project_and_version(
        project_name="ProjectName", version="v1.2.3", client=client
    )

    assert release.id() == "release-1"
    assert release.project_id() == "project-1"
    assert release.version() == "v1.2.3"


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
            response={"Items": [{"Version": "v0.1.9"}]},
        ),
    ]
)
def test_determine_latest_deploy_packages(prepared_release):
    # pylint: disable=protected-access
    assert prepared_release._determine_latest_deploy_packages(
        prepared_release.project_id()
    ) == [{"ActionName": "FirstAction", "Version": "v0.1.9"}]


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
        Request("get", "api/projects/ProjectName", response={"Id": "project-1"}),
        Request("head", "api/projects/project-1/releases/v1.2.3", response=True),
    ]
)
def test_skip_create_existing_release(client):
    rel = Release(client)
    rel.create("ProjectName", "v1.2.3", "Notes", auto_select_packages=False)
