from unittest.mock import Mock

import pytest

from velo_action.octopus import client, deployment, release
from velo_action.octopus.test_decorators import Request, mock_client_requests


@pytest.fixture
@mock_client_requests(
    [
        ("head", "api", True),
    ]
)
def octo() -> client.OctopusClient:
    return client.OctopusClient()


@pytest.fixture
@mock_client_requests(
    [
        Request("get", "api/projects/ProjectName", response={"Id": "project-1"}),
        Request(
            "get",
            "api/projects/project-1/releases/v1",
            response={
                "Id": "release-1",
                "ProjectId": "project-1",
                "Version": "v1",
                "Links": {
                    "ProjectVariableSnapshot": "api/variables/variableset-Projects-1-abc"
                },
            },
        ),
    ]
)
def release1(octo) -> release.Release:
    return release.Release.from_project_and_version(
        project_name="ProjectName", version="v1", client=octo
    )


@pytest.fixture
def deployment1(release1, octo) -> deployment.Deployment:
    return deployment.Deployment.from_release(release=release1, client=octo)


def test_init(octo):
    dep = deployment.Deployment(client=octo)
    assert dep.release() is None
    assert dep.release_id() == ""
    assert dep.project_id() == ""
    assert dep.id() == ""


@mock_client_requests(
    [
        ("get", "api/projects/ProjectName", {"Id": "project-1"}),
        (
            "get",
            "api/projects/project-1/releases/v1",
            {"Id": "release-1", "ProjectId": "project-1", "Version": "v1"},
        ),
    ]
)
def test_init_with_project_and_version(octo):
    dep = deployment.Deployment(project_name="ProjectName", version="v1", client=octo)
    assert isinstance(dep.release(), release.Release)
    assert dep.release_id() == "release-1"
    assert dep.project_id() == "project-1"
    assert dep.id() == ""


def test_from_release(release1, octo):
    dep = deployment.Deployment.from_release(release1, octo)
    assert dep.release() == release1
    assert dep.release_id() == release1.id() == "release-1"
    assert dep.project_id() == release1.project_id() == "project-1"
    assert dep.id() == ""


def test_project_id(release1, octo):
    dep = deployment.Deployment.from_release(release1, client=octo)
    assert dep.project_id() == "project-1"


def test_release_id(release1, octo):
    dep = deployment.Deployment.from_release(release1, client=octo)
    assert dep.release_id() == "release-1"


@mock_client_requests(
    [
        Request(
            "post",
            "api/deployments",
            payload={
                "EnvironmentId": "env-1",
                "ProjectId": "project-1",
                "ReleaseId": "release-1",
            },
            response={
                "Id": "deployment-1",
                "ReleaseId": "release-1",
                "ProjectId": "project-1",
            },
        )
    ]
)
def test_create(monkeypatch, deployment1):
    monkeypatch.setattr(
        client.OctopusClient, "lookup_environment_id", Mock(return_value="env-1")
    )
    deployment1.create(env_name="dev")
    assert deployment1.id() == "deployment-1"
    assert deployment1.release_id() == "release-1"
    assert deployment1.project_id() == "project-1"


@mock_client_requests(
    [
        Request(
            "post",
            "api/deployments",
            payload={
                "EnvironmentId": "env-1",
                "ProjectId": "project-1",
                "ReleaseId": "release-1",
                "TenantId": "tenant-1",
            },
            response={
                "Id": "deployment-1",
                "ReleaseId": "release-1",
                "ProjectId": "project-1",
            },
        )
    ]
)
def test_create_with_tenant(monkeypatch, deployment1):
    monkeypatch.setattr(
        client.OctopusClient, "lookup_environment_id", Mock(return_value="env-1")
    )
    monkeypatch.setattr(
        client.OctopusClient, "lookup_tenant_id", Mock(return_value="tenant-1")
    )
    deployment1.create(env_name="dev", tenant="TenantName")
    assert deployment1.id() == "deployment-1"


@mock_client_requests(
    [
        Request(
            "post",
            "api/deployments",
            payload={
                "EnvironmentId": "env-1",
                "ProjectId": "project-1",
                "ReleaseId": "release-1",
                "FormValues": {"12345-12345": "some value"},
            },
            response={
                "Id": "deployment-1",
                "ReleaseId": "release-1",
                "ProjectId": "project-1",
            },
        )
    ]
)
def test_create_with_variables(monkeypatch, deployment1):
    monkeypatch.setattr(
        client.OctopusClient, "lookup_environment_id", Mock(return_value="env-1")
    )
    monkeypatch.setattr(
        release.Release,
        "form_variable_id_mapping",
        Mock(return_value={"SomeVariable": "12345-12345"}),
    )
    deployment1.create(env_name="dev", variables={"SomeVariable": "some value"})
    assert deployment1.id() == "deployment-1"


@mock_client_requests(
    [
        Request(
            "post",
            "api/deployments",
            payload={
                "EnvironmentId": "env-1",
                "ProjectId": "project-1",
                "ReleaseId": "release-1",
            },
            response={"Id": "deployment-1"},
        ),
        Request(
            "get",
            "api/projects/project-1/progression",
            response={
                "Releases": [
                    {
                        "Release": {"Id": "release-1"},
                        "Deployments": {
                            "env-1": [
                                {
                                    "DeploymentId": "deployment-1",
                                    "IsCompleted": False,
                                    "HasWarningsOrErrors": False,
                                    "ErrorMessage": None,
                                    "State": "Success",
                                }
                            ]
                        },
                    }
                ],
            },
        ),
    ]
)
def test_create_with_wait(monkeypatch, deployment1):
    monkeypatch.setattr(
        client.OctopusClient, "lookup_environment_id", Mock(return_value="env-1")
    )
    deployment1.create("dev-env", wait_to_complete=True)
