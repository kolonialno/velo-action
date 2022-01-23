import functools
from unittest.mock import patch

from velo_action.octopus.client import OctopusClient


class Request:
    method: str
    path: str
    response: object
    payload: object

    def __init__(self, method, path, response=None, payload=None):
        self.method = method
        self.path = path
        self.response = response
        self.payload = payload


def mock_client_requests(registered_responses: list = None):
    """
    Decorator for mocking requests against the Octopus server

    Usage:
    @mock_client_requests([Request(),])

    Example:
    @mock_client_requests([
        Request("get", "api/projects/Projects-123", reponse={"Id: Projects-123"}),
        Request("post", "api/deployments",
            payload={"ReleaseId": "Releases-123"},
            reponse={"Id: Project-123"}
        ),
    ])
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if callable(registered_responses):
                # Decorator used without arguments
                responses = []
            else:
                # Local copy to prevent side effects
                responses = list(registered_responses)

            def perform_request(_self, method, path, data=None):
                nonlocal responses
                for i, req in enumerate(responses):
                    if method != req.method or path != req.path:
                        continue

                    if req.payload:
                        assert data == req.payload

                    responses.pop(i)
                    return req.response
                raise RuntimeError(
                    f"No request found for '{method}' '{path}'. "
                    f"Add it to @mock_client_requests([]):\n"
                    f'Request("{method}", "{path}", payload={data}, response={{}}),'
                )

            with patch.object(
                target=OctopusClient, attribute="_request", new=perform_request
            ):
                result = func(*args, **kwargs)

            if responses:
                raise RuntimeError(
                    f"Not all client responses have been used. Remaining: {responses}"
                )

            return result

        return wrapper

    if callable(registered_responses):
        return decorator(registered_responses)
    else:
        return decorator
