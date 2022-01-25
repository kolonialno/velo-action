import unittest.mock

import pytest

from velo_action.octopus.client import OctopusClient
from velo_action.octopus.test_decorators import Request, mock_client_requests


@pytest.fixture
@mock_client_requests(
    [
        Request("head", "api", response=True),
    ]
)
def octo():
    return OctopusClient()


@unittest.mock.patch(target="requests.request")
def test_init(request_mock: unittest.mock.Mock):
    request_mock.return_value = unittest.mock.Mock(
        **{"status_code": 200, "request.method": "head"}
    )

    OctopusClient(server="https://octopus/", api_key="ExampleApiKey")

    request_mock.assert_called_once_with(
        "head",
        "https://octopus/api",
        headers={"X-Octopus-ApiKey": "ExampleApiKey"},
        json=None,
    )


@mock_client_requests(
    [
        Request("get", "some/path", response={"Text": "Yohoo"}),
    ]
)
def test_get(octo):
    response = octo.get("some/path")
    assert response == {"Text": "Yohoo"}


@mock_client_requests(
    [
        Request("post", "some/path", response={"Text": "Ok"}),
    ]
)
def test_post(octo):
    assert octo.post("some/path", data="") == {"Text": "Ok"}


@mock_client_requests(
    [
        Request(
            "get", "api/environments/all", response=[{"Name": "DevEnv", "Id": "env-1"}]
        ),
    ]
)
def test_lookup_environment_id(octo):
    assert octo.lookup_environment_id("DevEnv") == "env-1"
    # Second call without mock ensures working cache
    assert octo.lookup_environment_id("DevEnv") == "env-1"


@mock_client_requests(
    [
        Request(
            "get", "api/environments/all", response=[{"Name": "DevEnv", "Id": "env-1"}]
        ),
    ]
)
def test_lookup_unknown_environment_id(octo):
    with pytest.raises(ValueError, match="'UnknownEnv' is unknown"):
        octo.lookup_environment_id("UnknownEnv")


@mock_client_requests(
    [
        Request("get", "api/projects/ProjectName", response={"Id": "project-1"}),
    ]
)
def test_lookup_project_id(octo):
    assert octo.lookup_project_id("ProjectName") == "project-1"
    # Second call without mock ensures working cache
    assert octo.lookup_project_id("ProjectName") == "project-1"


@mock_client_requests(
    [
        Request("get", "api/projects/UnknownProject", response=None),
    ]
)
def test_lookup_unknown_project_id(octo):
    with pytest.raises(ValueError, match="'UnknownProject' is unknown"):
        octo.lookup_project_id("UnknownProject")


@mock_client_requests(
    [
        Request(
            "get",
            "api/tenants/all",
            response=[{"Name": "TenantName", "Id": "tenant-1"}],
        ),
    ]
)
def test_lookup_tenant_id(octo):
    assert octo.lookup_tenant_id("TenantName") == "tenant-1"
    # Second call without mock ensures working cache
    assert octo.lookup_tenant_id("TenantName") == "tenant-1"


@mock_client_requests(
    [
        Request(
            "get",
            "api/tenants/all",
            response=[{"Name": "TenantName", "Id": "tenant-1"}],
        ),
    ]
)
def test_lookup_unknown_tenant_id(octo):
    with pytest.raises(ValueError, match="'UnknownTenant' is unknown"):
        octo.lookup_tenant_id("UnknownTenant")


def test_lookup_tenant_id_without_name(octo):
    assert octo.lookup_tenant_id(None) == ""
    assert octo.lookup_tenant_id("") == ""
