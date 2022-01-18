import unittest.mock

from velo_action.octopus.client import OctopusClient
from velo_action.octopus.test_decorators import mock_client_requests


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
        ("head", "api", None),
        ("get", "some/path", {"Text": "Yohoo"}),
    ]
)
def test_get():
    client = OctopusClient()
    response = client.get("some/path")
    assert response == {"Text": "Yohoo"}


@mock_client_requests(
    [
        ("head", "api", None),
        ("post", "some/path", {"Text": "Ok"}),
    ]
)
def test_post():
    client = OctopusClient()
    response = client.post("some/path", data="")
    assert response == {"Text": "Ok"}


@mock_client_requests(
    [
        ("head", "api", None),
        ("get", "api/projects/Project-1", {"Id": "project-1"}),
    ]
)
def test_lookup_project_id():
    client = OctopusClient()
    pid = client.lookup_project_id("Project-1")
    assert pid == "project-1"
